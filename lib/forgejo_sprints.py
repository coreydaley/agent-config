"""Forgejo-milestone-backed sprint tracking.

A sprint IS a Forgejo milestone in its primary repo:
  - milestone open   → sprint active   (Status: planned | in_progress)
  - milestone closed → sprint finished (Status: completed | skipped)
The milestone's attached issues are the work; its progress bar = completion.

Metadata the milestone has no native field for (session timestamp, fine status,
recommended/used model, fit verdict, participants) lives in a
delimited block in the milestone DESCRIPTION:

    ## Sprint metadata
    <!-- sprint-meta:start -->
    - **Session:** 2026-06-03T14-30-00
    - **Status:** in_progress
    - **Recommended model:** opus
    - **Model used:** opus
    - **Fit:** right_sized
    - **Participants:** claude, codex
    - **Advances:** §3 Data pipeline
    <!-- sprint-meta:end -->

This module owns the meta-block render/parse (pure, offline-testable) and the
`tea`/API operations against the Forgejo instance. Repo-less / cross-cutting
sprints (under ~/Reports/seeds, /forgejo, /no-repo) have no milestone home and
are NOT tracked here — they stay local-only.

It is BOTH a library (imported by the sprint-* skills) and a CLI. The sprint
workflow skills call it directly — there is no separate `sprints` skill:

    python3 ~/.claude/lib/forgejo_sprints.py --list
    python3 ~/.claude/lib/forgejo_sprints.py --get-doc <query>
    python3 ~/.claude/lib/forgejo_sprints.py --add <TS> "Title" --repo <o>/<r> --doc-file <SPRINT.md>

Run with --help for the full flag list.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

FORGEJO_URL = "https://mac-mini.example:3000"
TEA_CONFIG = Path.home() / "Library/Application Support/tea/config.yml"

META_START = "<!-- sprint-meta:start -->"
META_END = "<!-- sprint-meta:end -->"
RETRO_START = "<!-- sprint-retro:start -->"
RETRO_END = "<!-- sprint-retro:end -->"

VALID_STATUSES = ["planned", "in_progress", "completed", "skipped"]
OPEN_STATUSES = {"planned", "in_progress"}        # milestone open
CLOSED_STATUSES = {"completed", "skipped"}        # milestone closed
VALID_FITS = ["", "over_powered", "right_sized", "under_powered"]
VALID_PARTICIPANTS = {"claude", "codex"}

# Bare-name reports roots that have no repo (and therefore no milestone home).
_REPO_LESS_ROOTS = {"seeds", "forgejo", "no-repo"}


# --------------------------------------------------------------------------- #
# Record + meta-block (pure — no I/O, offline-testable)
# --------------------------------------------------------------------------- #
@dataclass
class Sprint:
    """One sprint, mirrored from a Forgejo milestone."""

    session: str            # timestamp like "2026-05-01T14-30-00" — the identity
    title: str
    status: str             # one of VALID_STATUSES
    repo: str = ""          # "<owner>/<repo>" the milestone lives in
    milestone_id: Optional[int] = None
    recommended_model: str = ""
    model: str = ""
    fit: str = ""
    participants: str = ""   # comma-separated subset of VALID_PARTICIPANTS
    prd_ref: str = ""        # PRD section this sprint advances (the "Advances" link)

    @property
    def is_open(self) -> bool:
        return self.status in OPEN_STATUSES

    def meta_block(self) -> str:
        """Render the delimited metadata block for the milestone description."""
        parts = "; ".join(sorted(p for p in
                                 (x.strip() for x in self.participants.split(","))
                                 if p)) if self.participants else ""
        lines = [
            "## Sprint metadata",
            META_START,
            f"- **Session:** {self.session}",
            f"- **Status:** {self.status}",
            f"- **Recommended model:** {self.recommended_model or '—'}",
            f"- **Model used:** {self.model or '—'}",
            f"- **Fit:** {self.fit or '—'}",
            f"- **Participants:** {parts or '—'}",
            f"- **Advances:** {self.prd_ref or '—'}",
            META_END,
        ]
        return "\n".join(lines)

    def upsert_into(self, description: str) -> str:
        """Return `description` with this sprint's meta block inserted/replaced.

        Replaces an existing block (between the markers, plus a preceding
        '## Sprint metadata' heading if present); otherwise appends it.
        """
        block = self.meta_block()
        if META_START in description and META_END in description:
            # Replace from an optional '## Sprint metadata' heading (or the
            # start marker) through the end marker.
            pat = re.compile(
                r"(?:#+\s*Sprint metadata\s*\n)?"
                + re.escape(META_START) + r".*?" + re.escape(META_END),
                re.DOTALL,
            )
            return pat.sub(block, description, count=1).rstrip() + "\n"
        sep = "" if description.endswith("\n") or not description else "\n\n"
        return (description + sep + "\n" + block + "\n").lstrip("\n")


def _strip_section(text: str, heading: str, start: str, end: str) -> str:
    """Remove an optional '## <heading>' line plus the start..end block."""
    pat = re.compile(
        r"\n*#+\s*" + re.escape(heading) + r"\s*\n" + re.escape(start) + r".*?" + re.escape(end),
        re.DOTALL,
    )
    return pat.sub("", text)


def extract_doc(description: str) -> str:
    """The SPRINT document carried in the milestone description — i.e. the
    description with the metadata footer and any Retrospective section removed."""
    d = _strip_section(description or "", "Retrospective", RETRO_START, RETRO_END)
    d = _strip_section(d, "Sprint metadata", META_START, META_END)
    return d.strip() + "\n" if d.strip() else ""


def set_retro(description: str, retro_md: str) -> str:
    """Insert/replace the '## Retrospective' section in a milestone description.

    Placed just before the '## Sprint metadata' footer so the metadata stays
    last. Replaces an existing retro section in place.
    """
    block = f"## Retrospective\n{RETRO_START}\n{retro_md.strip()}\n{RETRO_END}"
    if RETRO_START in description and RETRO_END in description:
        pat = re.compile(
            r"(?:#+\s*Retrospective\s*\n)?" + re.escape(RETRO_START) + r".*?" + re.escape(RETRO_END),
            re.DOTALL,
        )
        return pat.sub(block, description, count=1).rstrip() + "\n"
    # Insert before the metadata footer if present; otherwise append.
    anchor = description.find("## Sprint metadata")
    if anchor == -1:
        anchor = description.find(META_START)
    if anchor != -1:
        head, tail = description[:anchor].rstrip(), description[anchor:]
        return f"{head}\n\n{block}\n\n{tail}".rstrip() + "\n"
    return description.rstrip() + "\n\n" + block + "\n"


def parse_meta(description: str) -> dict:
    """Parse the meta block out of a milestone description. Empty dict if none."""
    if not description or META_START not in description:
        return {}
    body = description.split(META_START, 1)[1].split(META_END, 1)[0]
    out: dict = {}
    for line in body.splitlines():
        m = re.match(r"\s*-\s*\*\*(.+?):\*\*\s*(.*)\s*$", line)
        if not m:
            continue
        key = m.group(1).strip().lower().replace(" ", "_")
        val = m.group(2).strip()
        out[key] = "" if val == "—" else val
    return out


def sprint_from_milestone(repo: str, ms: dict) -> Optional[Sprint]:
    """Build a Sprint from a `tea milestones list --output json` entry.

    Returns None for milestones without a sprint-meta block (not our sprints).
    """
    desc = ms.get("description") or ms.get("Description") or ""
    meta = parse_meta(desc)
    session = meta.get("session", "")
    if not session:
        return None
    # Coarse open/closed from the milestone reconciles the fine status.
    ms_state = (ms.get("state") or ms.get("State") or "").lower()
    status = meta.get("status", "")
    if status not in VALID_STATUSES:
        status = "completed" if ms_state == "closed" else "in_progress"
    # If the milestone is closed but the meta still says open, trust closed.
    if ms_state == "closed" and status in OPEN_STATUSES:
        status = "completed"
    if ms_state == "open" and status in CLOSED_STATUSES:
        status = "in_progress"
    parts = ",".join(sorted(
        p for p in (x.strip().lower() for x in
                    re.split(r"[;,]", meta.get("participants", "")))
        if p in VALID_PARTICIPANTS
    ))
    return Sprint(
        session=session,
        title=ms.get("title") or ms.get("Title") or "",
        status=status,
        repo=repo,
        milestone_id=ms.get("id") or ms.get("ID"),
        recommended_model=meta.get("recommended_model", ""),
        model=meta.get("model_used", "") or meta.get("model", ""),
        fit=meta.get("fit", ""),
        participants=parts,
        prd_ref=meta.get("advances", ""),
    )


# --------------------------------------------------------------------------- #
# Repo / root mapping
# --------------------------------------------------------------------------- #
def repo_for_root(root: Path) -> Optional[str]:
    """Map a reports root to its '<owner>/<repo>', or None if repo-less.

    ~/Reports/<org>/<repo>/  → "<org>/<repo>"
    ~/Reports/seeds|forgejo|no-repo/ → None (no milestone home)
    """
    reports = Path.home() / "Reports"
    try:
        rel = root.resolve().relative_to(reports.resolve())
    except ValueError:
        return None
    parts = rel.parts
    if len(parts) == 1 and parts[0] in _REPO_LESS_ROOTS:
        return None
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return None


def session_dir_for(repo: str, session: str) -> Path:
    """The local working-copy session folder for a tracked sprint."""
    owner_repo = repo.split("/", 1)
    return Path.home() / "Reports" / owner_repo[0] / owner_repo[1] / "sprints" / session


# --------------------------------------------------------------------------- #
# Forgejo I/O (tea + raw API)
# --------------------------------------------------------------------------- #
def _token() -> str:
    if not TEA_CONFIG.exists():
        return ""
    f = False
    for line in TEA_CONFIG.read_text().splitlines():
        if "name: homelab" in line:
            f = True
        elif f and "token:" in line:
            return line.split("token:", 1)[1].strip()
    return ""


def _curl(method: str, path: str, body: Optional[dict] = None) -> tuple[int, str]:
    """Raw Forgejo API call. Returns (http_status, response_text)."""
    token = _token()
    args = ["curl", "-sk", "-o", "-", "-w", "\n%{http_code}",
            "-X", method, "-H", f"Authorization: token {token}"]
    if body is not None:
        args += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
    args.append(f"{FORGEJO_URL}/api/v1{path}")
    out = subprocess.run(args, capture_output=True, text=True).stdout
    nl = out.rfind("\n")
    text, code = (out[:nl], out[nl + 1:]) if nl >= 0 else (out, "0")
    try:
        return int(code.strip()), text
    except ValueError:
        return 0, text


def list_milestones(repo: str) -> list[dict]:
    """All milestones (any state) in a repo, as JSON dicts."""
    code, text = _curl("GET", f"/repos/{repo}/milestones?state=all&limit=100")
    if code != 200:
        return []
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return []


def list_sprints(repos: list[str]) -> list[Sprint]:
    """All tracked sprints across the given repos (those with a meta block)."""
    out: list[Sprint] = []
    for repo in repos:
        for ms in list_milestones(repo):
            s = sprint_from_milestone(repo, ms)
            if s:
                out.append(s)
    out.sort(key=lambda s: s.session)
    return out


def find_milestone_by_session(repo: str, session: str) -> Optional[dict]:
    for ms in list_milestones(repo):
        if parse_meta(ms.get("description", "")).get("session") == session:
            return ms
    return None


def create_sprint(sprint: Sprint, sprint_doc: str = "") -> Optional[dict]:
    """Create the milestone for a new sprint (open). The milestone DESCRIPTION
    is the SPRINT document itself (`sprint_doc`) with the metadata footer
    appended. Returns the milestone dict."""
    desc = sprint.upsert_into(sprint_doc or "")
    code, text = _curl("POST", f"/repos/{sprint.repo}/milestones",
                       {"title": sprint.title, "description": desc, "state": "open"})
    if code in (200, 201):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None
    return None


def get_doc(repo: str, session: str) -> Optional[str]:
    """The SPRINT document stored in a sprint's milestone description."""
    ms = find_milestone_by_session(repo, session)
    if not ms:
        return None
    return extract_doc(ms.get("description") or "")


def append_retro(repo: str, session: str, retro_md: str) -> bool:
    """Append/replace the Retrospective section in a sprint's milestone."""
    ms = find_milestone_by_session(repo, session)
    if not ms:
        return False
    new_desc = set_retro(ms.get("description") or "", retro_md)
    code, _ = _curl("PATCH", f"/repos/{repo}/milestones/{ms.get('id')}",
                    {"description": new_desc})
    return code == 200


def save_sprint(sprint: Sprint) -> bool:
    """Persist a sprint's state to its milestone: rewrite the meta block in the
    description and reconcile open/closed. Looks the milestone up by session."""
    ms = (find_milestone_by_session(sprint.repo, sprint.session)
          if sprint.milestone_id is None else _get_milestone(sprint.repo, sprint.milestone_id))
    if not ms:
        return False
    mid = ms.get("id")
    new_desc = sprint.upsert_into(ms.get("description") or "")
    new_state = "open" if sprint.is_open else "closed"
    code, _ = _curl("PATCH", f"/repos/{sprint.repo}/milestones/{mid}",
                    {"description": new_desc, "state": new_state})
    return code == 200


def _get_milestone(repo: str, mid: int) -> Optional[dict]:
    code, text = _curl("GET", f"/repos/{repo}/milestones/{mid}")
    if code != 200:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


# =========================================================================== #
# CLI — invoked directly by the sprint-* skills and for ad-hoc status queries.
# There is no separate `sprints` skill; this module IS the entry point.
#     python3 ~/.claude/lib/forgejo_sprints.py <flag> [args]
# =========================================================================== #
import sys  # noqa: E402

_CLI_HELP = """\
Sprint tracker — Forgejo-milestone-backed. A sprint IS a milestone in its
primary repo (open = active, closed = finished); metadata lives in the
milestone description's ## Sprint metadata block. Repo-less sprints (under
~/Reports/seeds, /forgejo, /no-repo) have no milestone and are NOT tracked.

Usage:
  forgejo_sprints.py --list [--status planned|in_progress|completed|skipped]
  forgejo_sprints.py --current                       # the in_progress sprint
  forgejo_sprints.py --next                          # next planned sprint
  forgejo_sprints.py --stats                         # status overview
  forgejo_sprints.py --add <TS> "Title" --repo <owner>/<repo>
                         [--doc-file <SPRINT.md>] [--recommended-model=M]
                         [--participants=claude,codex] [--prd-ref "<section>"]
  forgejo_sprints.py --start <query> [--model=M]     # → in_progress (stays open)
  forgejo_sprints.py --complete <query> [--model=M]  # → completed (close milestone)
  forgejo_sprints.py --skip <query>                  # → skipped (close milestone)
  forgejo_sprints.py --set-status <query> <status>
  forgejo_sprints.py --set-fit <query> <over_powered|right_sized|under_powered>
  forgejo_sprints.py --set-participants <query> <list>
  forgejo_sprints.py --get-doc <query>               # SPRINT doc from the description
  forgejo_sprints.py --append-retro <query> <file>   # append ## Retrospective
  forgejo_sprints.py --path <query>                  # local session-folder path

<query> is a session timestamp (full or prefix) or a title substring.
--root is accepted for back-compat and ignored (repos discovered from ~/Reports).
"""

_SYMBOL = {"planned": "○", "in_progress": "◐", "completed": "●", "skipped": "⊘"}


def _candidate_repos() -> list[str]:
    """Repos that may hold sprint milestones — derived from the local
    ~/Reports/<org>/<repo>/ roots (the bare-name roots have no repo)."""
    from sprint_ledger import discover_reports_roots
    repos, seen = [], set()
    for root in discover_reports_roots():
        repo = repo_for_root(root)
        if repo and repo not in seen:
            seen.add(repo)
            repos.append(repo)
    return repos


def _all_sprints(repo: Optional[str] = None) -> list["Sprint"]:
    return list_sprints([repo] if repo else _candidate_repos())


def _resolve(query: str, repo: Optional[str] = None) -> "Sprint":
    """Resolve a query to exactly one tracked sprint. Error on ambiguity/no-match."""
    sprints = _all_sprints(repo)
    exact = [s for s in sprints if s.session == query]
    if exact:
        return exact[0]
    pref = [s for s in sprints if s.session.startswith(query)]
    sub = [s for s in sprints if query.lower() in s.title.lower()]
    matches = pref or sub
    if not matches:
        raise ValueError(f"No tracked sprint matching: {query!r}")
    if len(matches) > 1:
        lines = [f"  {s.session}  {s.title}  ({s.repo})" for s in matches]
        raise ValueError(
            f"Ambiguous query {query!r} — {len(matches)} matches:\n" + "\n".join(lines)
            + "\nUse a more specific session timestamp or title fragment."
        )
    return matches[0]


def _print_row(s: "Sprint") -> None:
    sym = _SYMBOL.get(s.status, "?")
    extra = []
    if s.model:
        extra.append(s.model)
    if s.fit:
        extra.append(s.fit.replace("_", " "))
    tail = f"  [{', '.join(extra)}]" if extra else ""
    print(f"{sym} {s.session}  {s.title}  ({s.repo}){tail}")


def _print_verbose(s: "Sprint") -> None:
    print(f"{_SYMBOL.get(s.status, '?')} {s.session}  {s.title}")
    print()
    print(f"  {'Status':<14} {s.status.replace('_', ' ')}")
    print(f"  {'Repo':<14} {s.repo}")
    if s.model:
        rec = f"  (recommended: {s.recommended_model})" if s.recommended_model and s.recommended_model != s.model else ""
        print(f"  {'Model':<14} {s.model}{rec}")
    elif s.recommended_model:
        print(f"  {'Recommended':<14} {s.recommended_model}")
    if s.fit:
        print(f"  {'Fit':<14} {s.fit.replace('_', ' ')}")
    if s.participants:
        print(f"  {'Participants':<14} {s.participants}")
    if s.prd_ref:
        print(f"  {'Advances':<14} {s.prd_ref}")


def _cmd_list(status: Optional[str]) -> int:
    sprints = _all_sprints()
    if status:
        sprints = [s for s in sprints if s.status == status]
    if not sprints:
        print("No tracked sprints." + (f" (status={status})" if status else ""))
        return 0
    for s in sprints:
        _print_row(s)
    return 0


def _cmd_current() -> int:
    active = [s for s in _all_sprints() if s.status == "in_progress"]
    if not active:
        print("No in-progress sprint.")
        return 0
    for s in active:
        _print_verbose(s)
        print()
    return 0


def _cmd_next() -> int:
    planned = [s for s in _all_sprints() if s.status == "planned"]
    if not planned:
        print("No planned sprint queued.")
        return 0
    _print_verbose(planned[0])
    return 0


def _cmd_stats() -> int:
    sprints = _all_sprints()
    counts = {k: 0 for k in VALID_STATUSES}
    for s in sprints:
        counts[s.status] = counts.get(s.status, 0) + 1
    print(f"Tracked sprints: {len(sprints)}")
    for k in VALID_STATUSES:
        print(f"  {_SYMBOL[k]} {k.replace('_', ' '):<12} {counts[k]}")
    return 0


def _cmd_add(session: str, title: str, repo: Optional[str],
             recommended_model: str, participants: str, doc_file: Optional[str],
             prd_ref: str = "") -> int:
    if not repo:
        print(f"Sprint {session} has no primary repo — not tracked in Forgejo "
              f"(local-only). Skipping milestone creation.")
        return 0
    if find_milestone_by_session(repo, session):
        print(f"Sprint {session} already has a milestone in {repo}.")
        return 0
    sprint_doc = ""
    if doc_file:
        p = Path(doc_file).expanduser()
        if p.exists():
            sprint_doc = p.read_text()
    s = Sprint(session=session, title=title, status="planned", repo=repo,
               recommended_model=recommended_model, participants=participants,
               prd_ref=prd_ref)
    ms = create_sprint(s, sprint_doc)
    if not ms:
        print(f"ERROR: could not create milestone in {repo} (issues enabled? token?).",
              file=sys.stderr)
        return 1
    url = f"{FORGEJO_URL}/{repo}/milestone/{ms.get('id')}"
    print(f"Registered: {session}  {title}  → {url}")
    return 0


def _cmd_get_doc(query: str) -> int:
    s = _resolve(query)
    doc = get_doc(s.repo, s.session)
    if doc is None:
        print(f"No milestone doc for {query!r}.", file=sys.stderr)
        return 1
    sys.stdout.write(doc)
    return 0


def _cmd_append_retro(query: str, retro_file: str) -> int:
    s = _resolve(query)
    p = Path(retro_file).expanduser()
    if not p.exists():
        print(f"Retro file not found: {retro_file}", file=sys.stderr)
        return 1
    if not append_retro(s.repo, s.session, p.read_text()):
        print(f"ERROR: could not append retro to milestone for {s.session}.", file=sys.stderr)
        return 1
    print(f"Appended retrospective to {s.session}'s milestone.")
    return 0


def _mutate(query: str, **changes):
    s = _resolve(query)
    for k, v in changes.items():
        if v is not None:
            setattr(s, k, v)
    if not save_sprint(s):
        print(f"ERROR: could not update milestone for {s.session} in {s.repo}.", file=sys.stderr)
        return 1
    return s


def _cmd_start(query: str, model: Optional[str]) -> int:
    r = _mutate(query, status="in_progress", model=model)
    if isinstance(r, int):
        return r
    print(f"Started: {r.session}  {r.title}" + (f"  (model: {model})" if model else ""))
    return 0


def _cmd_complete(query: str, model: Optional[str]) -> int:
    r = _mutate(query, status="completed", model=model)
    if isinstance(r, int):
        return r
    print(f"Completed: {r.session}  {r.title}  → milestone closed")
    return 0


def _cmd_skip(query: str) -> int:
    r = _mutate(query, status="skipped")
    if isinstance(r, int):
        return r
    print(f"Skipped: {r.session}  {r.title}  → milestone closed")
    return 0


def _cmd_set_status(query: str, status: str) -> int:
    if status not in VALID_STATUSES:
        print(f"Invalid status {status!r}. One of: {VALID_STATUSES}", file=sys.stderr)
        return 1
    r = _mutate(query, status=status)
    if isinstance(r, int):
        return r
    print(f"Set status for {r.session}: {status}")
    return 0


def _cmd_set_fit(query: str, fit: str) -> int:
    if fit not in VALID_FITS or fit == "":
        print(f"Invalid fit {fit!r}. One of: {[v for v in VALID_FITS if v]}", file=sys.stderr)
        return 1
    r = _mutate(query, fit=fit)
    if isinstance(r, int):
        return r
    print(f"Set fit for {r.session}: {fit.replace('_', ' ')}")
    return 0


def _cmd_set_participants(query: str, participants: str) -> int:
    parts = ",".join(sorted(
        p for p in (x.strip().lower() for x in participants.split(","))
        if p in VALID_PARTICIPANTS))
    r = _mutate(query, participants=parts)
    if isinstance(r, int):
        return r
    print(f"Set participants for {r.session}: {parts or '(none)'}")
    return 0


def _cmd_path(query: str) -> int:
    s = _resolve(query)
    print(session_dir_for(s.repo, s.session))
    return 0


def _cli(argv: list[str]) -> int:
    if not argv or argv[0] in ("--help", "-h"):
        print(_CLI_HELP)
        return 0

    flag = argv[0]
    positional: list[str] = []
    opt = {"repo": None, "model": None, "recommended_model": "",
           "participants": "", "status": None, "doc_file": None, "prd_ref": ""}
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--repo":
            opt["repo"] = argv[i + 1]; i += 2; continue
        if a.startswith("--repo="):
            opt["repo"] = a.split("=", 1)[1]; i += 1; continue
        if a in ("--root",) or a.startswith("--root="):
            i += 2 if a == "--root" else 1; continue   # ignored (back-compat)
        if a == "--model" or a.startswith("--model="):
            opt["model"] = argv[i + 1] if a == "--model" else a.split("=", 1)[1]
            i += 2 if a == "--model" else 1; continue
        if a.startswith("--recommended-model="):
            opt["recommended_model"] = a.split("=", 1)[1]; i += 1; continue
        if a.startswith("--participants="):
            opt["participants"] = a.split("=", 1)[1]; i += 1; continue
        if a == "--prd-ref" or a.startswith("--prd-ref="):
            opt["prd_ref"] = argv[i + 1] if a == "--prd-ref" else a.split("=", 1)[1]
            i += 2 if a == "--prd-ref" else 1; continue
        if a == "--doc-file" or a.startswith("--doc-file="):
            opt["doc_file"] = argv[i + 1] if a == "--doc-file" else a.split("=", 1)[1]
            i += 2 if a == "--doc-file" else 1; continue
        if a == "--status" or a.startswith("--status="):
            opt["status"] = argv[i + 1] if a == "--status" else a.split("=", 1)[1]
            i += 2 if a == "--status" else 1; continue
        positional.append(a)
        i += 1

    try:
        if flag == "--list":
            return _cmd_list(opt["status"])
        if flag == "--current":
            return _cmd_current()
        if flag == "--next":
            return _cmd_next()
        if flag == "--stats":
            return _cmd_stats()
        if flag == "--add":
            if len(positional) < 2:
                print("Usage: --add <TS> <title> --repo <owner>/<repo> [--doc-file <SPRINT.md>] [--prd-ref <section>]"); return 1
            return _cmd_add(positional[0], positional[1], opt["repo"],
                            opt["recommended_model"], opt["participants"], opt["doc_file"],
                            opt["prd_ref"])
        if flag == "--get-doc":
            if not positional:
                print("Usage: --get-doc <query>"); return 1
            return _cmd_get_doc(positional[0])
        if flag == "--append-retro":
            if len(positional) < 2:
                print("Usage: --append-retro <query> <retro-file>"); return 1
            return _cmd_append_retro(positional[0], positional[1])
        if flag == "--start":
            if not positional:
                print("Usage: --start <query> [--model=M]"); return 1
            return _cmd_start(positional[0], opt["model"])
        if flag == "--complete":
            if not positional:
                print("Usage: --complete <query> [--model=M]"); return 1
            return _cmd_complete(positional[0], opt["model"])
        if flag == "--skip":
            if not positional:
                print("Usage: --skip <query>"); return 1
            return _cmd_skip(positional[0])
        if flag == "--set-status":
            if len(positional) < 2:
                print("Usage: --set-status <query> <status>"); return 1
            return _cmd_set_status(positional[0], positional[1])
        if flag == "--set-fit":
            if len(positional) < 2:
                print("Usage: --set-fit <query> <over_powered|right_sized|under_powered>"); return 1
            return _cmd_set_fit(positional[0], positional[1])
        if flag == "--set-participants":
            if len(positional) < 2:
                print("Usage: --set-participants <query> <comma-separated list>"); return 1
            return _cmd_set_participants(positional[0], positional[1])
        if flag == "--path":
            if not positional:
                print("Usage: --path <query>"); return 1
            return _cmd_path(positional[0])
        if flag == "--sync":
            print("Forgejo milestones are the source of truth — nothing to sync.")
            return 0
        print(f"Unknown flag: {flag}")
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
