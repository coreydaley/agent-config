#!/usr/bin/env python3
"""
Sprint Manager - CLI tool for tracking sprint progress.

Usage:
    python3 sprints.py stats                    # Show overview
    python3 sprints.py current                  # Show in_progress sprint
    python3 sprints.py next                     # Show next planned sprint
    python3 sprints.py add 003 "Sprint Title"   # Add new sprint
    python3 sprints.py start 001                # Mark as in_progress
    python3 sprints.py complete 001             # Mark as completed
    python3 sprints.py skip 001                 # Mark as skipped
    python3 sprints.py status 001 completed     # Set arbitrary status
    python3 sprints.py list [--status planned]  # List sprints
    python3 sprints.py sync                     # Sync from .md files
"""

import os
import sys
import re
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

    def __post_init__(self):
        self.sprint_id = str(int(self.sprint_id)).zfill(3)
        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {self.status}. Must be one of {self.VALID_STATUSES}")
        if self.fit not in self.VALID_FITS:
            raise ValueError(
                f"Invalid fit: {self.fit}. Must be one of {[v for v in self.VALID_FITS if v]}"
            )

    @property
    def sprint_number(self) -> int:
        return int(self.sprint_id)

    @property
    def doc_path(self) -> str:
        return f"./docs/sprints/*-sprint-plan-SPRINT-{self.sprint_id}.md"

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
            self.recommended_model, self.fit,
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
        )


class SprintLedger:
    """Manages the sprint ledger TSV file."""

    HEADER = (
        "sprint_id\ttitle\tstatus\tcreated_at\tupdated_at"
        "\tstarted_at\tcompleted_at\tmodel\trecommended_model\tfit"
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
            recommended_model: str = "") -> SprintEntry:
        sprint_id = str(int(sprint_id)).zfill(3)
        if sprint_id in self.entries:
            raise ValueError(f"Sprint {sprint_id} already exists")
        now = self._now()
        entry = SprintEntry(
            sprint_id=sprint_id, title=title, status=status,
            created_at=now, updated_at=now,
            recommended_model=recommended_model,
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


def print_verbose(entry: SprintEntry) -> None:
    """Render a single entry as a block with aligned key/value rows."""
    status_label = entry.status.replace("_", " ")
    when_label = _WHEN_LABELS.get(entry.status, "Updated")
    ts = _effective_timestamp(entry)
    print(f"{_symbol(entry.status)} Sprint {entry.sprint_id}  {entry.title}")
    print()
    print(f"  {'Status':<12} {status_label}")
    print(f"  {when_label:<12} {_relative_phrase(ts)}  ({_absolute_date(ts)})")
    # For completed sprints with both timestamps, show the duration it took.
    if entry.status == "completed" and entry.duration_seconds is not None:
        print(f"  {'Duration':<12} {_format_duration(entry.duration_seconds)}")
    if entry.model:
        override = ""
        if entry.recommended_model and entry.recommended_model != entry.model:
            override = f"  (recommended: {entry.recommended_model})"
        print(f"  {'Model':<12} {entry.model}{override}")
    elif entry.recommended_model:
        print(f"  {'Recommended':<12} {entry.recommended_model}")
    if entry.fit:
        print(f"  {'Fit':<12} {entry.fit.replace('_', ' ')}")
    print(f"  {'Doc':<12} {entry.doc_path}")


def cmd_stats(ledger: SprintLedger) -> None:
    counts = ledger.count_by_status()
    total = sum(counts.values())

    if total == 0:
        print("No sprints yet.")
        print("Run /sprint-plan to create the first.")
        return

    print(f"{total} sprint{'s' if total != 1 else ''} total")
    print()
    for status in ("completed", "in_progress", "planned", "skipped"):
        count = counts.get(status, 0)
        label = status.replace("_", " ")
        print(f"  {_symbol(status)}  {count:>2}  {label}")

    # Velocity line — only if we have measurable completed sprints
    records = ledger.velocity_records()
    if records:
        durations = [e.duration_seconds for e in records]
        avg = sum(durations) / len(durations)
        n = len(records)
        print()
        print(
            f"  {_bold_pad('Velocity', 9)}avg {_format_duration_compact(avg)} "
            f"over {n} completed sprint{'s' if n != 1 else ''}"
        )

    current = ledger.get_in_progress()
    next_sprint = ledger.get_next_planned()
    if current or next_sprint:
        print()
    if current:
        since = _relative_compact(current.started_at or current.updated_at)
        model_note = f", {current.model}" if current.model else ""
        print(
            f"  {_bold_pad('Current', 9)}{_symbol(current.status)} "
            f"{current.sprint_id}  {current.title}   (started {since}{model_note})"
        )
    if next_sprint:
        print(
            f"  {_bold_pad('Next', 9)}{_symbol(next_sprint.status)} "
            f"{next_sprint.sprint_id}  {next_sprint.title}"
        )


def cmd_current(ledger: SprintLedger) -> None:
    current = ledger.get_in_progress()
    if current:
        print_verbose(current)
        return
    print("No sprint in progress.")
    next_sprint = ledger.get_next_planned()
    if next_sprint:
        print(
            f"Next planned: {_symbol(next_sprint.status)} "
            f"{next_sprint.sprint_id}  {next_sprint.title}."
        )
        print("Run /sprint-work to start it.")
    else:
        print("Run /sprint-plan to create one.")


def cmd_next(ledger: SprintLedger) -> None:
    next_sprint = ledger.get_next_planned()
    if not next_sprint:
        print("No planned sprints.")
        print("Run /sprint-plan to create one.")
        return
    print_verbose(next_sprint)
    print()
    print("  Run /sprint-work to start it.")


def cmd_list(ledger: SprintLedger, status: Optional[str] = None) -> None:
    counts = ledger.count_by_status()
    total = sum(counts.values())

    if total == 0:
        print("No sprints yet.")
        print("Run /sprint-plan to create the first.")
        return

    entries = (
        ledger.get_by_status(status)
        if status
        else sorted(ledger.entries.values(), key=lambda e: e.sprint_number)
    )
    if not entries:
        print(f"No sprints with status '{status}'.")
        return

    # Summary header: overall counts (not filtered), so you see the whole picture
    header_parts = [
        f"{_symbol(s)} {counts[s]}"
        for s in ("completed", "in_progress", "planned", "skipped")
        if counts.get(s, 0) > 0
    ]
    print(f"{total} sprint{'s' if total != 1 else ''}  " + "   ".join(header_parts))
    print()

    # Right-align status-dependent info to the end of the longest title column:
    # in_progress shows elapsed time, completed shows total duration.
    def _right(entry: SprintEntry) -> str:
        if entry.status == "in_progress":
            return _relative_compact(entry.started_at or entry.updated_at)
        if entry.status == "completed" and entry.duration_seconds is not None:
            return _format_duration_compact(entry.duration_seconds)
        return ""

    max_title = max(len(e.title) for e in entries)
    for entry in entries:
        right = _right(entry)
        if right:
            padded = entry.title.ljust(max_title)
            print(f"  {_symbol(entry.status)} {entry.sprint_id}  {padded}   {right}")
        else:
            print(f"  {_symbol(entry.status)} {entry.sprint_id}  {entry.title}")


def cmd_add(
    ledger: SprintLedger, sprint_id: str, title: str, recommended_model: str = ""
) -> None:
    entry = ledger.add(sprint_id, title, recommended_model=recommended_model)
    ledger.save()
    rec_note = f" (recommended: {entry.recommended_model})" if entry.recommended_model else ""
    print(f"Added sprint {entry.sprint_id}: {entry.title}{rec_note}")


def cmd_set_fit(ledger: SprintLedger, sprint_id: str, fit: str) -> None:
    entry = ledger.set_fit(sprint_id, fit)
    ledger.save()
    print(f"Set fit for sprint {entry.sprint_id}: {entry.fit.replace('_', ' ')}")


def cmd_start(ledger: SprintLedger, sprint_id: str, model: Optional[str] = None) -> None:
    entry = ledger.update_status(sprint_id, "in_progress", model)
    ledger.save()
    model_note = f" ({entry.model})" if entry.model else ""
    print(f"Started sprint {entry.sprint_id}: {entry.title}{model_note}")


def cmd_complete(ledger: SprintLedger, sprint_id: str, model: Optional[str] = None) -> None:
    entry = ledger.update_status(sprint_id, "completed", model)
    ledger.save()
    duration_note = (
        f" in {_format_duration(entry.duration_seconds)}"
        if entry.duration_seconds is not None
        else ""
    )
    print(f"Completed sprint {entry.sprint_id}: {entry.title}{duration_note}")


def cmd_velocity(ledger: SprintLedger) -> None:
    """Detailed velocity breakdown across completed sprints."""
    records = ledger.velocity_records()
    if not records:
        print("Not enough data to measure velocity.")
        print("Velocity needs at least one completed sprint with a recorded start and end.")
        return

    durations_sorted = sorted(e.duration_seconds for e in records)
    n = len(durations_sorted)
    mean = sum(durations_sorted) / n
    median = (
        durations_sorted[n // 2]
        if n % 2
        else (durations_sorted[n // 2 - 1] + durations_sorted[n // 2]) / 2
    )

    print(f"Velocity — {n} completed sprint{'s' if n != 1 else ''} with duration data")
    print()
    print(f"  {'Mean':<10} {_format_duration(mean)}")
    print(f"  {'Median':<10} {_format_duration(median)}")
    print(f"  {'Fastest':<10} {_format_duration(durations_sorted[0])}")
    print(f"  {'Slowest':<10} {_format_duration(durations_sorted[-1])}")
    if n >= 10:
        p90 = durations_sorted[int(n * 0.9) - 1]
        print(f"  {'p90':<10} {_format_duration(p90)}")

    if n >= 2:
        k = min(3, n)
        recent = [e.duration_seconds for e in records[-k:]]
        print(f"  {'Last ' + str(k):<10} avg {_format_duration(sum(recent) / k)}")

    # Recommendation accuracy — only count sprints where a recommendation was made
    with_rec = [e for e in records if e.recommended_model and e.model]
    if with_rec:
        matches = sum(1 for e in with_rec if e.recommended_model == e.model)
        pct = (matches / len(with_rec)) * 100
        print(
            f"  {'Rec match':<10} {matches}/{len(with_rec)} "
            f"({pct:.0f}% accepted recommendation)"
        )

    # Breakdown by model (tier), with fit verdicts when present
    by_model: dict[str, list[SprintEntry]] = {}
    for e in records:
        if e.model:
            by_model.setdefault(e.model, []).append(e)
    if by_model:
        print()
        print("  By model:")
        for model in sorted(by_model):
            entries = by_model[model]
            durations = [e.duration_seconds for e in entries]
            avg = sum(durations) / len(durations)
            fits = [e.fit for e in entries if e.fit]
            fit_summary = ""
            if fits:
                fit_counts: dict[str, int] = {}
                for f in fits:
                    fit_counts[f] = fit_counts.get(f, 0) + 1
                parts = [
                    f"{count} {verdict.replace('_', '-')}"
                    for verdict, count in sorted(fit_counts.items())
                ]
                fit_summary = f"   ({', '.join(parts)})"
            print(
                f"    {model:<8}  {len(entries)} sprint{'s' if len(entries) != 1 else ''}, "
                f"avg {_format_duration(avg)}{fit_summary}"
            )


def cmd_skip(ledger: SprintLedger, sprint_id: str) -> None:
    entry = ledger.update_status(sprint_id, "skipped")
    ledger.save()
    print(f"Skipped sprint {entry.sprint_id}: {entry.title}")


def cmd_status(ledger: SprintLedger, sprint_id: str, status: str) -> None:
    entry = ledger.update_status(sprint_id, status)
    ledger.save()
    print(f"Updated sprint {entry.sprint_id} to {entry.status}")


def cmd_sync(ledger: SprintLedger) -> None:
    changes = ledger.sync_from_docs()
    if changes:
        ledger.save()
        print("Sync complete:")
        for change in changes:
            print(f"  {change}")
    else:
        print("No changes needed")


HELP_TEXT = """\
/sprints — manage the sprint record

Usage:
  /sprints <flag> [args]

Action flags (mutually exclusive):
  --stats                       Show overview of all sprints
  --current                     Show the in-progress sprint
  --next                        Show the next planned sprint
  --list                        List all sprints (combine with --status to filter)
  --velocity                    Velocity statistics across completed sprints
  --add NNN "Title"             Add a new sprint entry
                                  (optional --recommended-model=<name>)
  --start NNN [--model=<name>]  Mark sprint NNN as in_progress; record model if given
  --complete NNN [--model=<n>]  Mark sprint NNN as completed
  --skip NNN                    Mark sprint NNN as skipped
  --set-status NNN <status>     Set arbitrary status for sprint NNN
  --set-fit NNN <verdict>       Record post-sprint fit (over_powered /
                                  right_sized / under_powered) from the retro
  --sync                        Sync from *-sprint-plan-SPRINT-*.md files
  --help, -h                    Show this help and exit

Modifier flags:
  --status=<status>             Filter for --list (e.g. --list --status=planned)
  --model=<name>                Record the model (opus/sonnet/haiku) for a sprint.
                                Pairs with --start (primary) or --complete.
  --recommended-model=<name>    What sprint-plan suggested at planning time.
                                Pairs with --add.

Valid statuses: planned, in_progress, completed, skipped

Data file: ./docs/sprints/sprints.tsv (relative to cwd; created if missing)

Full documentation: ~/.claude/skills/sprints/SKILL.md"""


def main() -> int:
    if len(sys.argv) < 2:
        print(HELP_TEXT)
        return 1

    if sys.argv[1] in ("--help", "-h", "help"):
        print(HELP_TEXT)
        return 0

    flag = sys.argv[1]
    # Collect non-flag positional arguments after the action flag, while also
    # extracting modifier flags (--status for --list, --model for --start/--complete).
    positional: list[str] = []
    status_filter: Optional[str] = None
    model_modifier: Optional[str] = None
    recommended_model_modifier: Optional[str] = None
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg.startswith("--status="):
            status_filter = arg.split("=", 1)[1]
        elif arg == "--status" and i + 1 < len(sys.argv):
            status_filter = sys.argv[i + 1]
            i += 1
        elif arg.startswith("--recommended-model="):
            recommended_model_modifier = arg.split("=", 1)[1]
        elif arg == "--recommended-model" and i + 1 < len(sys.argv):
            recommended_model_modifier = sys.argv[i + 1]
            i += 1
        elif arg.startswith("--model="):
            model_modifier = arg.split("=", 1)[1]
        elif arg == "--model" and i + 1 < len(sys.argv):
            model_modifier = sys.argv[i + 1]
            i += 1
        else:
            positional.append(arg)
        i += 1

    ledger = SprintLedger(get_ledger_path()).load()

    try:
        if flag == "--stats":
            cmd_stats(ledger)
        elif flag == "--current":
            cmd_current(ledger)
        elif flag == "--next":
            cmd_next(ledger)
        elif flag == "--list":
            cmd_list(ledger, status_filter)
        elif flag == "--velocity":
            cmd_velocity(ledger)
        elif flag == "--add":
            if len(positional) < 2:
                print(
                    "Usage: sprints.py --add <sprint_id> <title> "
                    "[--recommended-model=<name>]"
                )
                return 1
            cmd_add(
                ledger, positional[0], " ".join(positional[1:]),
                recommended_model_modifier or "",
            )
        elif flag == "--start":
            if not positional:
                print("Usage: sprints.py --start <sprint_id> [--model=<name>]")
                return 1
            cmd_start(ledger, positional[0], model_modifier)
        elif flag == "--complete":
            if not positional:
                print("Usage: sprints.py --complete <sprint_id> [--model=<name>]")
                return 1
            cmd_complete(ledger, positional[0], model_modifier)
        elif flag == "--skip":
            if not positional:
                print("Usage: sprints.py --skip <sprint_id>")
                return 1
            cmd_skip(ledger, positional[0])
        elif flag == "--set-status":
            if len(positional) < 2:
                print("Usage: sprints.py --set-status <sprint_id> <status>")
                return 1
            cmd_status(ledger, positional[0], positional[1])
        elif flag == "--set-fit":
            if len(positional) < 2:
                print("Usage: sprints.py --set-fit <sprint_id> <over_powered|right_sized|under_powered>")
                return 1
            cmd_set_fit(ledger, positional[0], positional[1])
        elif flag == "--sync":
            cmd_sync(ledger)
        else:
            print(f"Unknown flag: {flag}")
            print(HELP_TEXT)
            return 1
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
