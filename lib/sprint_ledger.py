"""
Sprint ledger — shared library for sprint tracking.

Provides SprintEntry/SprintLedger data model and display helpers used by:
- ~/.claude/skills/sprints/scripts/cli.py — sprint manager CLI
- ~/.claude/lib/commit.py — commit planner (reads participants for sprint-artifact commits)

Sprints are keyed by their session timestamp (e.g. "2026-05-01T14-30-00"),
which corresponds to the folder name under ~/Reports/<org>/<repo>/sprints/.
The session is unique, chronological, and the canonical identifier — no
separate sprint number layer.
"""

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional


# --- Display helpers -------------------------------------------------

SYMBOLS = {
    "planned": "◯",
    "in_progress": "◐",
    "completed": "●",
    "skipped": "⊘",
}


class _C:
    GREEN = "\033[32m"
    CYAN = "\033[36m"
    BLUE = "\033[34m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


_STATUS_COLORS = {
    "planned": _C.BLUE,
    "in_progress": _C.CYAN,
    "completed": _C.GREEN,
    "skipped": _C.DIM,
}


def _use_color() -> bool:
    """Auto-detect color support: NO_COLOR env var disables; otherwise require TTY."""
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def _colorize(text: str, color: str) -> str:
    return f"{color}{text}{_C.RESET}" if _use_color() else text


def _symbol(status: str) -> str:
    return _colorize(SYMBOLS.get(status, "?"), _STATUS_COLORS.get(status, ""))


def _bold_pad(text: str, width: int) -> str:
    """Bold the text, then pad with spaces so the visible width is `width`."""
    return _colorize(text, _C.BOLD) + " " * max(0, width - len(text))


def _parse_iso(iso_ts: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _relative_compact(iso_ts: str) -> str:
    """Compact form: '3d', '5h', '2w', 'Apr 20'. For --list / --stats rows."""
    dt = _parse_iso(iso_ts)
    if dt is None:
        return iso_ts
    delta = datetime.now(timezone.utc) - dt
    if delta < timedelta(minutes=1):
        return "just now"
    if delta < timedelta(hours=1):
        return f"{int(delta.total_seconds() // 60)}m"
    if delta < timedelta(days=1):
        return f"{int(delta.total_seconds() // 3600)}h"
    if delta < timedelta(days=14):
        return f"{delta.days}d"
    if delta < timedelta(days=60):
        return f"{delta.days // 7}w"
    return dt.strftime("%b %d")


def _relative_phrase(iso_ts: str) -> str:
    """Human phrase: '3 days ago', '2 weeks ago'. For verbose blocks."""
    dt = _parse_iso(iso_ts)
    if dt is None:
        return iso_ts
    delta = datetime.now(timezone.utc) - dt
    if delta < timedelta(minutes=1):
        return "just now"
    if delta < timedelta(hours=1):
        n = int(delta.total_seconds() // 60)
        return f"{n} minute{'s' if n != 1 else ''} ago"
    if delta < timedelta(days=1):
        n = int(delta.total_seconds() // 3600)
        return f"{n} hour{'s' if n != 1 else ''} ago"
    if delta < timedelta(days=14):
        return f"{delta.days} day{'s' if delta.days != 1 else ''} ago"
    if delta < timedelta(days=60):
        w = delta.days // 7
        return f"{w} week{'s' if w != 1 else ''} ago"
    return dt.strftime("%b %d, %Y")


def _absolute_date(iso_ts: str) -> str:
    dt = _parse_iso(iso_ts)
    return dt.strftime("%Y-%m-%d") if dt else iso_ts


def _format_duration(seconds: float) -> str:
    """Verbose form: '2d 3h', '45m', '8h 12m'. For --complete output and --velocity."""
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        return f"{int(seconds // 60)}m"
    if seconds < 86400:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}h {m}m" if m else f"{h}h"
    d = int(seconds // 86400)
    h = int((seconds % 86400) // 3600)
    return f"{d}d {h}h" if h else f"{d}d"


def _format_duration_compact(seconds: float) -> str:
    """Compact form: just the biggest unit. For --list and --stats rows."""
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        return f"{int(seconds // 60)}m"
    if seconds < 86400:
        return f"{int(seconds // 3600)}h"
    return f"{int(seconds // 86400)}d"


def _short_session(session: str) -> str:
    """Compact display of a session timestamp: 'May 01 14:30'."""
    dt = _parse_iso(session.replace("T", " ").replace("-", ":", 2)
                    if session.count("-") >= 5 else session)
    # Sessions have form YYYY-MM-DDTHH-MM-SS; convert to ISO for parsing.
    if dt is None and len(session) == 19 and session[10] == "T":
        # Convert YYYY-MM-DDTHH-MM-SS → YYYY-MM-DDTHH:MM:SS
        iso_form = session[:13] + ":" + session[14:16] + ":" + session[17:]
        dt = _parse_iso(iso_form)
    return dt.strftime("%b %d %H:%M") if dt else session


# --- End display helpers ---------------------------------------------


@dataclass
class SprintEntry:
    """A single sprint entry in the ledger, keyed by session timestamp."""

    VALID_STATUSES = ["planned", "in_progress", "completed", "skipped"]
    VALID_FITS = ["", "over_powered", "right_sized", "under_powered"]
    VALID_PARTICIPANTS = {"claude", "codex"}

    session: str  # primary key — timestamp like "2026-05-01T14-30-00"
    title: str
    status: str
    created_at: str
    updated_at: str
    started_at: str = ""
    completed_at: str = ""
    model: str = ""
    recommended_model: str = ""
    fit: str = ""
    participants: str = ""  # comma-separated subset of VALID_PARTICIPANTS

    def __post_init__(self):
        if not self.session:
            raise ValueError("session is required")
        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {self.status}. Must be one of {self.VALID_STATUSES}")
        if self.fit not in self.VALID_FITS:
            raise ValueError(
                f"Invalid fit: {self.fit}. Must be one of {[v for v in self.VALID_FITS if v]}"
            )
        # Normalize participants: trim whitespace, lowercase, dedupe, sort.
        if self.participants:
            parts = [p.strip().lower() for p in self.participants.split(",") if p.strip()]
            invalid = [p for p in parts if p not in self.VALID_PARTICIPANTS]
            if invalid:
                raise ValueError(
                    f"Invalid participants: {invalid}. "
                    f"Must be from {sorted(self.VALID_PARTICIPANTS)}"
                )
            self.participants = ",".join(sorted(set(parts)))

    @property
    def doc_path(self) -> str:
        """Path to this sprint's SPRINT.md, relative to the reports root."""
        return f"sprints/{self.session}/SPRINT.md"

    @property
    def participant_list(self) -> list[str]:
        """Participants as a sorted list; empty list if none recorded."""
        return [p for p in self.participants.split(",") if p] if self.participants else []

    @property
    def duration_seconds(self) -> Optional[float]:
        """Elapsed seconds between started_at and completed_at, if both set."""
        if not self.started_at or not self.completed_at:
            return None
        start = _parse_iso(self.started_at)
        end = _parse_iso(self.completed_at)
        if not start or not end:
            return None
        delta = (end - start).total_seconds()
        return delta if delta >= 0 else None

    def to_tsv(self) -> str:
        return "\t".join([
            self.session, self.title, self.status,
            self.created_at, self.updated_at,
            self.started_at, self.completed_at, self.model,
            self.recommended_model, self.fit, self.participants,
        ])

    @classmethod
    def from_tsv(cls, line: str) -> "SprintEntry":
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 5:
            raise ValueError(f"Invalid TSV line: {line}")
        return cls(
            session=parts[0], title=parts[1], status=parts[2],
            created_at=parts[3], updated_at=parts[4],
            started_at=parts[5] if len(parts) > 5 else "",
            completed_at=parts[6] if len(parts) > 6 else "",
            model=parts[7] if len(parts) > 7 else "",
            recommended_model=parts[8] if len(parts) > 8 else "",
            fit=parts[9] if len(parts) > 9 else "",
            participants=parts[10] if len(parts) > 10 else "",
        )


class SprintLedger:
    """Manages the sprint ledger TSV file. Keyed by session timestamp."""

    HEADER = (
        "session\ttitle\tstatus\tcreated_at\tupdated_at"
        "\tstarted_at\tcompleted_at\tmodel\trecommended_model\tfit"
        "\tparticipants"
    )

    def __init__(self, path: Path):
        self.path = path
        self.entries: dict[str, SprintEntry] = {}

    def load(self) -> "SprintLedger":
        if not self.path.exists():
            return self
        with open(self.path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines[1:]:  # Skip header
            line = line.strip()
            if not line:
                continue
            entry = SprintEntry.from_tsv(line)
            self.entries[entry.session] = entry
        return self

    def save(self) -> None:
        # Sort chronologically by session (which is a sortable timestamp).
        sorted_entries = sorted(self.entries.values(), key=lambda e: e.session)
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(self.HEADER + "\n")
            for entry in sorted_entries:
                f.write(entry.to_tsv() + "\n")

    def _now(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def find(self, query: str) -> list[SprintEntry]:
        """Resolve a user-supplied query to a list of matching entries.

        Match strategy, in priority order:
        1. Exact session match
        2. Session prefix match (e.g. "2026-05-01" → matches sessions starting with that date)
        3. Title substring match (case-insensitive)

        Caller decides how to disambiguate when multiple results are returned.
        """
        if query in self.entries:
            return [self.entries[query]]
        prefix_matches = [e for e in self.entries.values() if e.session.startswith(query)]
        if prefix_matches:
            return prefix_matches
        q_lower = query.lower()
        return [e for e in self.entries.values() if q_lower in e.title.lower()]

    def add(self, session: str, title: str, status: str = "planned",
            recommended_model: str = "", participants: str = "") -> SprintEntry:
        if session in self.entries:
            raise ValueError(f"Sprint with session '{session}' already exists")
        now = self._now()
        entry = SprintEntry(
            session=session, title=title, status=status,
            created_at=now, updated_at=now,
            recommended_model=recommended_model,
            participants=participants,
        )
        self.entries[session] = entry
        return entry

    def set_fit(self, session: str, fit: str) -> SprintEntry:
        if session not in self.entries:
            raise ValueError(f"Sprint '{session}' not found")
        if fit not in SprintEntry.VALID_FITS or fit == "":
            valid = [v for v in SprintEntry.VALID_FITS if v]
            raise ValueError(f"Invalid fit: {fit!r}. Must be one of {valid}")
        entry = self.entries[session]
        entry.fit = fit
        entry.updated_at = self._now()
        return entry

    def set_participants(self, session: str, participants: str) -> SprintEntry:
        """Replace the participants list for a sprint."""
        if session not in self.entries:
            raise ValueError(f"Sprint '{session}' not found")
        entry = self.entries[session]
        # Round-trip via SprintEntry to normalize.
        temp = SprintEntry(
            session=entry.session, title=entry.title, status=entry.status,
            created_at=entry.created_at, updated_at=entry.updated_at,
            participants=participants,
        )
        entry.participants = temp.participants
        entry.updated_at = self._now()
        return entry

    def update_status(self, session: str, status: str, model: Optional[str] = None) -> SprintEntry:
        if session not in self.entries:
            raise ValueError(f"Sprint '{session}' not found")
        if status not in SprintEntry.VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}. Must be one of {SprintEntry.VALID_STATUSES}")
        entry = self.entries[session]
        now = self._now()
        if status == "in_progress":
            # Only stamp started_at on the FIRST transition into in_progress.
            # Re-running --start on an already-in-progress sprint (resume after
            # crash, manual re-invocation) shouldn't reset the timer — that
            # corrupts duration and velocity stats.
            if entry.status != "in_progress" or not entry.started_at:
                entry.started_at = now
            entry.completed_at = ""
        elif status == "completed":
            entry.completed_at = now
        entry.status = status
        entry.updated_at = now
        if model:
            entry.model = model
        return entry

    def velocity_records(self) -> list[SprintEntry]:
        """Return completed sprints with both started_at and completed_at set.
        Sorted by completion time (oldest first). Skipped sprints excluded."""
        records = [
            e for e in self.entries.values()
            if e.status == "completed" and e.duration_seconds is not None
        ]
        records.sort(key=lambda e: e.completed_at)
        return records

    def get_next_planned(self) -> Optional[SprintEntry]:
        """Return the chronologically-oldest planned sprint, or None."""
        planned = [e for e in self.entries.values() if e.status == "planned"]
        return min(planned, key=lambda e: e.session) if planned else None

    def get_in_progress(self) -> Optional[SprintEntry]:
        in_progress = [e for e in self.entries.values() if e.status == "in_progress"]
        return in_progress[0] if in_progress else None

    def get_by_status(self, status: str) -> list[SprintEntry]:
        if status not in SprintEntry.VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}. Must be one of {SprintEntry.VALID_STATUSES}")
        return sorted(
            [e for e in self.entries.values() if e.status == status],
            key=lambda e: e.session,
        )

    def count_by_status(self) -> dict[str, int]:
        counts = {s: 0 for s in SprintEntry.VALID_STATUSES}
        for entry in self.entries.values():
            counts[entry.status] += 1
        return counts

    def sync_from_docs(self) -> list[str]:
        """Scan ./sprints/<TS>/SPRINT.md files (relative to ledger.tsv parent)
        and update the ledger. Title is the first heading (`# Title`); the
        session is the parent folder name."""
        changes = []
        # Accept "# Title" or "# Sprint 001: Title" (legacy) — strip the
        # legacy prefix if present.
        heading_pattern = re.compile(r"^#\s+(.+)$", re.MULTILINE)
        legacy_prefix = re.compile(r"^Sprint\s+\d+\s*[:—–-]\s*", re.IGNORECASE)
        sprints_dir = self.path.parent / "sprints"
        if not sprints_dir.is_dir():
            return changes
        for sprint_md in sorted(sprints_dir.glob("*/SPRINT.md")):
            session = sprint_md.parent.name
            content = sprint_md.read_text(encoding="utf-8")
            heading_match = heading_pattern.search(content)
            if not heading_match:
                continue
            title = legacy_prefix.sub("", heading_match.group(1).strip()).strip()
            if not title:
                continue
            if session not in self.entries:
                self.add(session, title)
                changes.append(f"Added: {session} — {title}")
            else:
                existing = self.entries[session]
                if existing.title != title:
                    existing.title = title
                    existing.updated_at = self._now()
                    changes.append(f"Updated: {session} — {title}")
        return changes


def get_reports_base(override: Optional[Path] = None) -> Path:
    """Resolve the reports base directory.

    Resolution order:
    1. `override` argument (used by callers that already know the root, e.g.
       /sprint-work passing --root derived from the sprint's session_dir).
    2. SPRINT_REPORTS_ROOT env var.
    3. ~/Reports/<org>/<repo>/ from the cwd's upstream/origin remote.
    4. ~/Reports/no-repo/ fallback when cwd isn't a git repo or has no
       usable remote.

    Prefers `upstream` over `origin` because `origin` typically points at a
    personal fork under our GitHub workflow, which would land reports under
    the fork's path rather than the source repo's."""
    if override is not None:
        base = Path(override).expanduser()
        base.mkdir(parents=True, exist_ok=True)
        return base
    env_override = os.environ.get("SPRINT_REPORTS_ROOT")
    if env_override:
        base = Path(env_override).expanduser()
        base.mkdir(parents=True, exist_ok=True)
        return base
    org_repo = "no-repo"
    for remote_name in ("upstream", "origin"):
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", remote_name],
                capture_output=True, text=True, check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
        remote = result.stdout.strip()
        # Strip leading host (handles both ssh and https forms) and trailing .git
        match = re.search(r"github\.com[:/](.+?)(?:\.git)?$", remote)
        if match:
            org_repo = match.group(1)
            break
    base = Path.home() / "Reports" / org_repo
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_ledger_path(reports_base: Optional[Path] = None) -> Path:
    """Resolve ledger.tsv under the given reports base (or auto-detected)."""
    return get_reports_base(reports_base) / "ledger.tsv"


def get_sprints_dir(reports_base: Optional[Path] = None) -> Path:
    """Resolve sprints/ under the given reports base (or auto-detected)."""
    sprints_dir = get_reports_base(reports_base) / "sprints"
    sprints_dir.mkdir(parents=True, exist_ok=True)
    return sprints_dir


def discover_reports_roots() -> list[Path]:
    """Find every ledger-bearing root under ~/Reports/.

    Used by /sprints when no explicit --root is passed. Supports two layouts:
    - `<root>/ledger.tsv` for the bare-name roots (seeds/, linear/, no-repo/)
    - `<org>/<repo>/ledger.tsv` for standard repo-scoped roots

    Returns absolute paths to the ledger-bearing directories. Empty list if
    ~/Reports/ doesn't exist yet.
    """
    base = Path.home() / "Reports"
    if not base.is_dir():
        return []
    roots: list[Path] = []
    for level1 in sorted(base.iterdir()):
        if not level1.is_dir():
            continue
        if (level1 / "ledger.tsv").exists():
            roots.append(level1)
            continue
        # Two-level <org>/<repo>/ledger.tsv
        for level2 in sorted(level1.iterdir()):
            if level2.is_dir() and (level2 / "ledger.tsv").exists():
                roots.append(level2)
    return roots


def find_across_roots(
    query: str,
    *,
    prefer_in_progress: bool = True,
    prefer_recent: bool = True,
) -> list[tuple["SprintEntry", Path]]:
    """Search every discovered root for entries matching `query`.

    Returns list of (entry, root_path) tuples, **sorted by canonical
    tie-break order**:
    1. `prefer_in_progress`: entries whose status is `in_progress` first.
    2. `prefer_recent`: among ties, most-recent session timestamp first
       (lexicographic on session — works because session is YYYY-MM-DDTHH-MM-SS).

    Both preferences are on by default — the canonical workflow assumes
    "the active sprint, then the most-recent." Callers that want unsorted
    results pass `prefer_in_progress=False, prefer_recent=False`. Empty
    list if no match.

    Centralizing tie-break here means every consumer (CLI auto-detect,
    self-review init's LINEAR.md walker, sprint-work's load-context) gets
    the same order without reimplementing the logic.
    """
    matches: list[tuple["SprintEntry", Path]] = []
    for root in discover_reports_roots():
        ledger = SprintLedger(root / "ledger.tsv").load()
        for entry in ledger.find(query):
            matches.append((entry, root))

    if not matches:
        return matches

    # Stable sort: secondary key first (recent), then primary (in_progress).
    if prefer_recent:
        matches.sort(key=lambda m: m[0].session, reverse=True)
    if prefer_in_progress:
        matches.sort(key=lambda m: 0 if m[0].status == "in_progress" else 1)

    return matches


# --- Shared display helpers for entry formatting ---------------------

_WHEN_LABELS = {
    "planned": "Added",
    "in_progress": "Started",
    "completed": "Completed",
    "skipped": "Skipped",
}


def _effective_timestamp(entry: SprintEntry) -> str:
    """Pick the most meaningful timestamp for the entry's status.
    Falls back to updated_at for entries predating the started_at/completed_at
    schema."""
    if entry.status == "in_progress":
        return entry.started_at or entry.updated_at
    if entry.status == "completed":
        return entry.completed_at or entry.updated_at
    if entry.status == "skipped":
        return entry.updated_at
    return entry.created_at  # planned
