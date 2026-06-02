"""Plane-shaped markdown schema.

Data model + YAML-frontmatter read/write for the Plane workflow mirrored
to markdown under ~/Reports/<org>/<repo>/. Used by the plane-* skills.

Layout under one workspace:

  ~/Reports/<org>/                          # Workspace dir
    WORKSPACE.md
    <repo>/                                 # Project dir (one per app/repo)
      PROJECT.md
      work-items/<ID>.md                    # canonical work item store
      cycles/<DATE>--cycle-NNN/CYCLE.md     # time-boxed
      modules/<slug>.md                     # topical, long-lived
      epics/<slug>.md                       # cross-cycle arcs
      milestones/<slug>.md                  # ship targets
      pages/<slug>.md                       # ADRs, design docs
      audits/<TS>-<name>/                   # audit input (existing layout)
        REPORT.md                           # produced by audit-* skills
        work-items/<ID>.md                  # ingested, audit-scoped
        INGEST.md                           # ingest manifest
        PROMOTE.md                          # promotion manifest

Work items in audits/<TS>/work-items/ are scoped to that audit run.
plane-audit-promote lifts them into the project-level work-items/ pool,
matching by (audit_type, audit_id) to re-open or update existing entries.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field, fields, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml


# --- Enums (as frozen sets — kept simple, no Enum class) -------------

STATES = frozenset({
    "backlog",      # not yet scheduled
    "unstarted",    # scheduled, not begun
    "started",      # in progress
    "completed",    # done
    "cancelled",    # explicitly closed without doing the work
    "deferred",     # scheduled for a future milestone (e.g. v0.2)
})

# Allowed state transitions. Re-audit promotion can move completed -> started
# (re-opened). Cancelled is a sink — promotion does NOT re-open.
TRANSITIONS = {
    "backlog":   {"unstarted", "started", "cancelled", "deferred"},
    "unstarted": {"started", "backlog", "cancelled", "deferred"},
    "started":   {"completed", "unstarted", "cancelled", "deferred"},
    "completed": {"started"},  # re-open only
    "cancelled": set(),         # terminal
    "deferred":  {"backlog", "unstarted", "started", "cancelled"},
}

PRIORITIES = frozenset({"urgent", "high", "medium", "low", "none"})

SOURCES = frozenset({"audit", "bug", "feature", "chore", "manual"})

# Map audit REPORT.md severity → priority. Audit findings flow into work
# items with this mapping applied at ingest time.
SEVERITY_TO_PRIORITY = {
    "critical":      "urgent",
    "high":          "high",
    "medium":        "medium",
    "low":           "low",
    "informational": "none",
}


# --- Frontmatter helpers --------------------------------------------

_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?(.*)\Z", re.DOTALL)


def split_frontmatter(text: str) -> tuple[dict, str]:
    """Split YAML frontmatter from body. Returns ({}, text) if absent."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm = yaml.safe_load(m.group(1)) or {}
    body = m.group(2)
    return fm, body


def join_frontmatter(meta: dict, body: str) -> str:
    """Serialize ({}, body) back to a YAML-frontmatter markdown document.
    Drops None values and empty lists/dicts so the frontmatter stays terse."""
    cleaned = {k: v for k, v in meta.items()
               if v is not None and v != [] and v != {}}
    yml = yaml.safe_dump(cleaned, sort_keys=False, allow_unicode=True).rstrip()
    body = body.lstrip("\n")
    return f"---\n{yml}\n---\n\n{body}" if body else f"---\n{yml}\n---\n"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- Slugify ---------------------------------------------------------

def slugify(name: str) -> str:
    """Filesystem-safe slug. Lowercased, alphanumeric + hyphens only."""
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip()).strip("-").lower()
    return s or "untitled"


# --- Org / repo / paths ---------------------------------------------

def resolve_org_repo(project_cwd: Path) -> tuple[str, str]:
    """Resolve (org, repo) from upstream/origin git remote of project_cwd.
    Falls back to ('local', basename) for non-git or no-remote dirs."""
    try:
        for remote in ("upstream", "origin"):
            try:
                url = subprocess.check_output(
                    ["git", "-C", str(project_cwd), "remote", "get-url", remote],
                    stderr=subprocess.DEVNULL, text=True).strip()
                if url:
                    # ssh: git@github.com:org/repo.git  https: https://github.com/org/repo(.git)?
                    m = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?/?$", url)
                    if m:
                        return m.group(1), m.group(2)
            except subprocess.CalledProcessError:
                continue
    except FileNotFoundError:
        pass
    return "local", project_cwd.name


def reports_base() -> Path:
    return Path.home() / "Reports"


def workspace_dir(org: str) -> Path:
    return reports_base() / org


def project_dir(org: str, repo: str) -> Path:
    return reports_base() / org / repo


# --- Workspace / Project metadata -----------------------------------

@dataclass
class Workspace:
    id: str                        # org slug (= directory name)
    name: str                      # display name
    created: str = field(default_factory=now_iso)
    description: str = ""

    @classmethod
    def load(cls, org: str) -> Optional["Workspace"]:
        p = workspace_dir(org) / "WORKSPACE.md"
        if not p.exists():
            return None
        meta, body = split_frontmatter(p.read_text())
        meta.setdefault("id", org)
        meta.setdefault("name", org)
        return cls(
            id=meta["id"], name=meta["name"],
            created=meta.get("created", now_iso()),
            description=body.strip(),
        )

    def save(self) -> Path:
        p = workspace_dir(self.id) / "WORKSPACE.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        meta = {"id": self.id, "name": self.name, "created": self.created}
        body = self.description.rstrip() + "\n" if self.description else ""
        p.write_text(join_frontmatter(meta, body))
        return p


@dataclass
class Project:
    id: str                        # repo slug (= directory name)
    name: str                      # display name (e.g. "Purrchiver")
    workspace: str                 # org slug
    state: str = "active"          # active | archived
    repo_url: str = ""
    ship_target: str = ""          # e.g. "v0.1 MAS submission"
    created: str = field(default_factory=now_iso)
    description: str = ""

    @classmethod
    def load(cls, org: str, repo: str) -> Optional["Project"]:
        p = project_dir(org, repo) / "PROJECT.md"
        if not p.exists():
            return None
        meta, body = split_frontmatter(p.read_text())
        meta.setdefault("id", repo)
        meta.setdefault("name", repo)
        meta.setdefault("workspace", org)
        return cls(
            id=meta["id"], name=meta["name"], workspace=meta["workspace"],
            state=meta.get("state", "active"),
            repo_url=meta.get("repo_url", ""),
            ship_target=meta.get("ship_target", ""),
            created=meta.get("created", now_iso()),
            description=body.strip(),
        )

    def save(self) -> Path:
        p = project_dir(self.workspace, self.id) / "PROJECT.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        meta = {
            "id": self.id, "name": self.name, "workspace": self.workspace,
            "state": self.state, "repo_url": self.repo_url,
            "ship_target": self.ship_target, "created": self.created,
        }
        body = self.description.rstrip() + "\n" if self.description else ""
        p.write_text(join_frontmatter(meta, body))
        return p


# --- Work item -------------------------------------------------------

@dataclass
class WorkItem:
    """One work item. Canonical file under <project_dir>/work-items/<id>.md;
    audit-scoped copy under <audit_dir>/work-items/<id>.md."""
    id: str                              # e.g. SEC-001 (audit-derived)
    title: str
    project: str                         # repo slug
    workspace: str                       # org slug

    state: str = "backlog"
    priority: str = "none"
    labels: list[str] = field(default_factory=list)

    cycle: Optional[str] = None          # cycle dir slug
    module: Optional[str] = None         # module slug
    epic: Optional[str] = None           # epic slug
    milestone: Optional[str] = None      # milestone slug

    source: str = "manual"
    source_ref: Optional[str] = None     # relative path or URL
    audit_id: Optional[str] = None       # audit-internal ID (= id, kept for clarity)
    audit_type: Optional[str] = None     # apple-security, apple-performance, ...
    audit_severity: Optional[str] = None # critical | high | medium | low | informational

    assignee: Optional[str] = None
    estimate_points: Optional[int] = None
    deferral_reason: Optional[str] = None
    deferral_target: Optional[str] = None
    landed_in: Optional[str] = None      # commit SHA

    location_hint: Optional[str] = None  # source file/line referenced by audit
    created: str = field(default_factory=now_iso)
    updated: str = field(default_factory=now_iso)

    # Body sections — stored as raw markdown text.
    description: str = ""
    acceptance: str = ""
    activity_log: list[str] = field(default_factory=list)

    # --- (de)serialization ------------------------------------------

    @classmethod
    def from_text(cls, text: str) -> "WorkItem":
        meta, body = split_frontmatter(text)
        # Body is parsed into description / acceptance / activity_log by
        # H2 section headers; missing sections default to empty.
        sections = _split_sections(body)
        wi = cls(
            id=meta["id"], title=meta["title"],
            project=meta["project"], workspace=meta["workspace"],
            state=meta.get("state", "backlog"),
            priority=meta.get("priority", "none"),
            labels=list(meta.get("labels") or []),
            cycle=meta.get("cycle"),
            module=meta.get("module"),
            epic=meta.get("epic"),
            milestone=meta.get("milestone"),
            source=meta.get("source", "manual"),
            source_ref=meta.get("source_ref"),
            audit_id=meta.get("audit_id"),
            audit_type=meta.get("audit_type"),
            audit_severity=meta.get("audit_severity"),
            assignee=meta.get("assignee"),
            estimate_points=meta.get("estimate_points"),
            deferral_reason=meta.get("deferral_reason"),
            deferral_target=meta.get("deferral_target"),
            landed_in=meta.get("landed_in"),
            location_hint=meta.get("location_hint"),
            created=meta.get("created", now_iso()),
            updated=meta.get("updated", now_iso()),
            description=sections.get("description", "").strip(),
            acceptance=sections.get("acceptance criteria", "").strip(),
            activity_log=_parse_activity_log(sections.get("activity log", "")),
        )
        return wi

    def to_text(self) -> str:
        meta = {
            "id": self.id, "title": self.title,
            "project": self.project, "workspace": self.workspace,
            "state": self.state, "priority": self.priority,
            "labels": self.labels or None,
            "cycle": self.cycle, "module": self.module,
            "epic": self.epic, "milestone": self.milestone,
            "source": self.source, "source_ref": self.source_ref,
            "audit_id": self.audit_id, "audit_type": self.audit_type,
            "audit_severity": self.audit_severity,
            "assignee": self.assignee,
            "estimate_points": self.estimate_points,
            "deferral_reason": self.deferral_reason,
            "deferral_target": self.deferral_target,
            "landed_in": self.landed_in,
            "location_hint": self.location_hint,
            "created": self.created, "updated": self.updated,
        }
        parts = []
        if self.description:
            parts.append(f"## Description\n\n{self.description.strip()}\n")
        if self.acceptance:
            parts.append(f"## Acceptance criteria\n\n{self.acceptance.strip()}\n")
        if self.activity_log:
            log = "\n".join(f"- {e}" for e in self.activity_log)
            parts.append(f"## Activity log\n\n{log}\n")
        body = "\n".join(parts)
        return join_frontmatter(meta, body)

    @classmethod
    def load(cls, path: Path) -> "WorkItem":
        return cls.from_text(path.read_text())

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.updated = now_iso()
        path.write_text(self.to_text())
        return path

    # --- Helpers ----------------------------------------------------

    def append_activity(self, msg: str) -> None:
        self.activity_log.append(f"{now_iso()} — {msg}")

    def validate(self) -> list[str]:
        errs = []
        if self.state not in STATES:
            errs.append(f"state {self.state!r} not in {sorted(STATES)}")
        if self.priority not in PRIORITIES:
            errs.append(f"priority {self.priority!r} not in {sorted(PRIORITIES)}")
        if self.source not in SOURCES:
            errs.append(f"source {self.source!r} not in {sorted(SOURCES)}")
        if not self.id or not self.title:
            errs.append("id and title are required")
        return errs


def _split_sections(body: str) -> dict[str, str]:
    """Split a markdown body into a {lowercase-header: section-text} dict.
    Only H2 (##) headers are split on; lower headers stay inside their parent."""
    sections: dict[str, str] = {}
    current = None
    buf: list[str] = []
    for line in body.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = m.group(1).strip().lower()
            buf = []
        else:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf).strip()
    return sections


def _parse_activity_log(text: str) -> list[str]:
    """Activity log is a bulleted list. Strip the leading `- `."""
    out = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("- "):
            out.append(line[2:].strip())
        elif line:
            out.append(line)
    return out


# --- Work item directories ------------------------------------------

def project_work_item_path(org: str, repo: str, work_item_id: str) -> Path:
    return project_dir(org, repo) / "work-items" / f"{work_item_id}.md"


def audit_work_item_path(audit_dir: Path, work_item_id: str) -> Path:
    return audit_dir / "work-items" / f"{work_item_id}.md"


def list_project_work_items(org: str, repo: str) -> list[Path]:
    wi_dir = project_dir(org, repo) / "work-items"
    if not wi_dir.exists():
        return []
    return sorted(wi_dir.glob("*.md"))


# --- Cycle / Module / Epic / Milestone ------------------------------

@dataclass
class Cycle:
    """Time-boxed batch of work items. Cycle dir name encodes the date
    + sequential index for filesystem sort: cycles/<YYYY-MM-DD>--cycle-NNN/."""
    id: str                        # e.g. "2026-05-22--cycle-001"
    name: str                      # display name, e.g. "Purrchiver v0.1 — Cycle 1"
    project: str                   # repo slug
    workspace: str                 # org slug
    goal: str = ""
    state: str = "planned"         # planned | active | completed | cancelled
    start_date: str = ""           # YYYY-MM-DD
    end_date: str = ""             # YYYY-MM-DD
    exit_criteria: list[str] = field(default_factory=list)
    created: str = field(default_factory=now_iso)
    updated: str = field(default_factory=now_iso)
    description: str = ""

    @classmethod
    def dir_for(cls, org: str, repo: str, cycle_id: str) -> Path:
        return project_dir(org, repo) / "cycles" / cycle_id

    @classmethod
    def path_for(cls, org: str, repo: str, cycle_id: str) -> Path:
        return cls.dir_for(org, repo, cycle_id) / "CYCLE.md"

    @classmethod
    def load(cls, org: str, repo: str, cycle_id: str) -> Optional["Cycle"]:
        p = cls.path_for(org, repo, cycle_id)
        if not p.exists():
            return None
        meta, body = split_frontmatter(p.read_text())
        return cls(
            id=meta.get("id", cycle_id),
            name=meta.get("name", cycle_id),
            project=meta.get("project", repo),
            workspace=meta.get("workspace", org),
            goal=meta.get("goal", ""),
            state=meta.get("state", "planned"),
            start_date=str(meta.get("start_date", "")),
            end_date=str(meta.get("end_date", "")),
            exit_criteria=list(meta.get("exit_criteria") or []),
            created=meta.get("created", now_iso()),
            updated=meta.get("updated", now_iso()),
            description=body.strip(),
        )

    def save(self) -> Path:
        p = self.path_for(self.workspace, self.project, self.id)
        p.parent.mkdir(parents=True, exist_ok=True)
        self.updated = now_iso()
        meta = {
            "id": self.id, "name": self.name,
            "project": self.project, "workspace": self.workspace,
            "goal": self.goal, "state": self.state,
            "start_date": self.start_date, "end_date": self.end_date,
            "exit_criteria": self.exit_criteria or None,
            "created": self.created, "updated": self.updated,
        }
        body = self.description.rstrip() + "\n" if self.description else ""
        p.write_text(join_frontmatter(meta, body))
        return p

    @classmethod
    def list(cls, org: str, repo: str) -> list["Cycle"]:
        cdir = project_dir(org, repo) / "cycles"
        if not cdir.exists():
            return []
        out = []
        for d in sorted(cdir.iterdir()):
            if d.is_dir() and (d / "CYCLE.md").exists():
                c = cls.load(org, repo, d.name)
                if c:
                    out.append(c)
        return out


def _entity_md(kind: str) -> str:
    """Flat-file kind/slug → filename: modules/<slug>.md, epics/<slug>.md, etc."""
    return {"module": "modules", "epic": "epics", "milestone": "milestones"}[kind]


@dataclass
class _NamedEntity:
    """Shared base for Module / Epic / Milestone — flat files under
    <project>/<kind>s/<slug>.md, simple metadata + description."""
    id: str
    name: str
    project: str
    workspace: str
    state: str = "active"
    created: str = field(default_factory=now_iso)
    updated: str = field(default_factory=now_iso)
    description: str = ""

    KIND: str = ""  # overridden by subclasses

    @classmethod
    def path_for(cls, org: str, repo: str, slug: str) -> Path:
        return project_dir(org, repo) / _entity_md(cls.KIND) / f"{slug}.md"

    @classmethod
    def load(cls, org: str, repo: str, slug: str):
        p = cls.path_for(org, repo, slug)
        if not p.exists():
            return None
        meta, body = split_frontmatter(p.read_text())
        return cls(
            id=meta.get("id", slug),
            name=meta.get("name", slug),
            project=meta.get("project", repo),
            workspace=meta.get("workspace", org),
            state=meta.get("state", "active"),
            created=meta.get("created", now_iso()),
            updated=meta.get("updated", now_iso()),
            description=body.strip(),
        )

    def save(self) -> Path:
        p = self.path_for(self.workspace, self.project, self.id)
        p.parent.mkdir(parents=True, exist_ok=True)
        self.updated = now_iso()
        meta = {
            "id": self.id, "name": self.name, "kind": self.KIND,
            "project": self.project, "workspace": self.workspace,
            "state": self.state,
            "created": self.created, "updated": self.updated,
        }
        body = self.description.rstrip() + "\n" if self.description else ""
        p.write_text(join_frontmatter(meta, body))
        return p


@dataclass
class Module(_NamedEntity):
    KIND: str = "module"


@dataclass
class Epic(_NamedEntity):
    KIND: str = "epic"


@dataclass
class Milestone(_NamedEntity):
    KIND: str = "milestone"


# --- State-transition helper ----------------------------------------

def validate_transition(from_state: str, to_state: str) -> Optional[str]:
    """None if allowed; error message if not."""
    if from_state == to_state:
        return None
    if from_state not in STATES:
        return f"unknown source state {from_state!r}"
    allowed = TRANSITIONS.get(from_state, set())
    if to_state not in allowed:
        return (f"transition {from_state} → {to_state} not allowed; "
                f"allowed from {from_state}: {sorted(allowed) or '(terminal)'}")
    return None


def find_existing_work_item(
    org: str, repo: str, audit_type: str, audit_id: str
) -> Optional[WorkItem]:
    """Locate a project-pool work item that matches (audit_type, audit_id).
    Used by promotion to decide create-vs-update."""
    for p in list_project_work_items(org, repo):
        try:
            wi = WorkItem.load(p)
        except Exception:
            continue
        if wi.audit_type == audit_type and wi.audit_id == audit_id:
            return wi
    return None
