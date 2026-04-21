"""
Sprint ledger — shared library for sprint tracking.

Provides SprintEntry/SprintLedger data model and display helpers used by:
- ~/.claude/skills/sprints/scripts/sprints.py — sprint manager CLI
- ~/.claude/lib/commit.py — commit planner (reads participants for sprint-artifact commits)

Extracted from the original self-contained sprints.py so the schema lives
in one place. Any script that touches the ledger imports from here.
"""

import os
import re
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


# --- End display helpers ---------------------------------------------


@dataclass
class SprintEntry:
    """A single sprint entry in the ledger."""

    VALID_STATUSES = ["planned", "in_progress", "completed", "skipped"]
    VALID_FITS = ["", "over_powered", "right_sized", "under_powered"]
    VALID_PARTICIPANTS = {"claude", "codex"}

    sprint_id: str
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
        self.sprint_id = str(int(self.sprint_id)).zfill(3)
        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {self.status}. Must be one of {self.VALID_STATUSES}")
        if self.fit not in self.VALID_FITS:
            raise ValueError(
                f"Invalid fit: {self.fit}. Must be one of {[v for v in self.VALID_FITS if v]}"
            )
        # Normalize participants: trim whitespace, lowercase, dedupe, sort.
        # Empty string is valid (no planning workers ran, e.g. --base mode).
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
    def sprint_number(self) -> int:
        return int(self.sprint_id)

    @property
    def doc_path(self) -> str:
        return f"./docs/sprints/*-sprint-plan-SPRINT-{self.sprint_id}.md"

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
            self.sprint_id, self.title, self.status,
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
            sprint_id=parts[0], title=parts[1], status=parts[2],
            created_at=parts[3], updated_at=parts[4],
            started_at=parts[5] if len(parts) > 5 else "",
            completed_at=parts[6] if len(parts) > 6 else "",
            model=parts[7] if len(parts) > 7 else "",
            recommended_model=parts[8] if len(parts) > 8 else "",
            fit=parts[9] if len(parts) > 9 else "",
            participants=parts[10] if len(parts) > 10 else "",
        )


class SprintLedger:
    """Manages the sprint ledger TSV file."""

    HEADER = (
        "sprint_id\ttitle\tstatus\tcreated_at\tupdated_at"
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
            self.entries[entry.sprint_id] = entry
        return self

    def save(self) -> None:
        sorted_entries = sorted(self.entries.values(), key=lambda e: e.sprint_number)
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(self.HEADER + "\n")
            for entry in sorted_entries:
                f.write(entry.to_tsv() + "\n")

    def _now(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def add(self, sprint_id: str, title: str, status: str = "planned",
            recommended_model: str = "", participants: str = "") -> SprintEntry:
        sprint_id = str(int(sprint_id)).zfill(3)
        if sprint_id in self.entries:
            raise ValueError(f"Sprint {sprint_id} already exists")
        now = self._now()
        entry = SprintEntry(
            sprint_id=sprint_id, title=title, status=status,
            created_at=now, updated_at=now,
            recommended_model=recommended_model,
            participants=participants,
        )
        self.entries[sprint_id] = entry
        return entry

    def set_fit(self, sprint_id: str, fit: str) -> SprintEntry:
        sprint_id = str(int(sprint_id)).zfill(3)
        if sprint_id not in self.entries:
            raise ValueError(f"Sprint {sprint_id} not found")
        if fit not in SprintEntry.VALID_FITS or fit == "":
            valid = [v for v in SprintEntry.VALID_FITS if v]
            raise ValueError(f"Invalid fit: {fit!r}. Must be one of {valid}")
        entry = self.entries[sprint_id]
        entry.fit = fit
        entry.updated_at = self._now()
        return entry

    def set_participants(self, sprint_id: str, participants: str) -> SprintEntry:
        """Replace the participants list for a sprint. Whitespace and case
        are normalized by SprintEntry.__post_init__ via a re-construction."""
        sprint_id = str(int(sprint_id)).zfill(3)
        if sprint_id not in self.entries:
            raise ValueError(f"Sprint {sprint_id} not found")
        entry = self.entries[sprint_id]
        # Normalize via round-trip: assign raw, then post-init-style cleanup.
        # Easier: build a temp SprintEntry just to validate/normalize.
        temp = SprintEntry(
            sprint_id=entry.sprint_id, title=entry.title, status=entry.status,
            created_at=entry.created_at, updated_at=entry.updated_at,
            participants=participants,
        )
        entry.participants = temp.participants
        entry.updated_at = self._now()
        return entry


    def update_status(self, sprint_id: str, status: str, model: Optional[str] = None) -> SprintEntry:
        sprint_id = str(int(sprint_id)).zfill(3)
        if sprint_id not in self.entries:
            raise ValueError(f"Sprint {sprint_id} not found")
        if status not in SprintEntry.VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}. Must be one of {SprintEntry.VALID_STATUSES}")
        entry = self.entries[sprint_id]
        now = self._now()
        # Record timing on the transitions that matter. Re-starts overwrite
        # started_at (per design: duration = most recent attempt only).
        if status == "in_progress":
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
        planned = [e for e in self.entries.values() if e.status == "planned"]
        return min(planned, key=lambda e: e.sprint_number) if planned else None

    def get_in_progress(self) -> Optional[SprintEntry]:
        in_progress = [e for e in self.entries.values() if e.status == "in_progress"]
        return in_progress[0] if in_progress else None

    def get_by_status(self, status: str) -> list[SprintEntry]:
        if status not in SprintEntry.VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}. Must be one of {SprintEntry.VALID_STATUSES}")
        return sorted([e for e in self.entries.values() if e.status == status], key=lambda e: e.sprint_number)

    def count_by_status(self) -> dict[str, int]:
        counts = {s: 0 for s in SprintEntry.VALID_STATUSES}
        for entry in self.entries.values():
            counts[entry.status] += 1
        return counts

    def sync_from_docs(self) -> list[str]:
        changes = []
        title_pattern = re.compile(r"^# Sprint: (.+)$", re.MULTILINE)
        filename_pattern = re.compile(r"SPRINT-(\d+)\.md$")
        for md_file in self.path.parent.glob("*-sprint-plan-SPRINT-*.md"):
            match = filename_pattern.search(md_file.name)
            if not match:
                continue
            sprint_id = match.group(1).zfill(3)
            content = md_file.read_text(encoding="utf-8")
            title_match = title_pattern.search(content)
            title = title_match.group(1).strip() if title_match else f"Sprint {sprint_id}"
            if sprint_id not in self.entries:
                self.add(sprint_id, title)
                changes.append(f"Added: {sprint_id} - {title}")
            else:
                existing = self.entries[sprint_id]
                if existing.title != title:
                    existing.title = title
                    existing.updated_at = self._now()
                    changes.append(f"Updated title: {sprint_id} - {title}")
        return changes


def get_ledger_path() -> Path:
    """Resolve the sprints TSV to ./docs/sprints/sprints.tsv relative to cwd."""
    sprint_dir = Path.cwd() / "docs" / "sprints"
    sprint_dir.mkdir(parents=True, exist_ok=True)
    return sprint_dir / "sprints.tsv"


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
