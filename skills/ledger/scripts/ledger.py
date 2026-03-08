#!/usr/bin/env python3
"""
Sprint Ledger Manager - CLI tool for tracking sprint progress.

Usage:
    python3 ledger.py stats                    # Show overview
    python3 ledger.py current                  # Show in_progress sprint
    python3 ledger.py next                     # Show next planned sprint
    python3 ledger.py add 003 "Sprint Title"   # Add new sprint
    python3 ledger.py start 001                # Mark as in_progress
    python3 ledger.py complete 001             # Mark as completed
    python3 ledger.py skip 001                 # Mark as skipped
    python3 ledger.py status 001 completed     # Set arbitrary status
    python3 ledger.py list [--status planned]  # List sprints
    python3 ledger.py sync                     # Sync from .md files
"""

import sys
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class SprintEntry:
    """A single sprint entry in the ledger."""

    VALID_STATUSES = ["planned", "in_progress", "completed", "skipped"]

    sprint_id: str
    title: str
    status: str
    created_at: str
    updated_at: str

    def __post_init__(self):
        self.sprint_id = str(int(self.sprint_id)).zfill(3)
        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {self.status}. Must be one of {self.VALID_STATUSES}")

    @property
    def sprint_number(self) -> int:
        return int(self.sprint_id)

    @property
    def doc_path(self) -> str:
        return f"docs/sprints/SPRINT-{self.sprint_id}.md"

    def to_tsv(self) -> str:
        return f"{self.sprint_id}\t{self.title}\t{self.status}\t{self.created_at}\t{self.updated_at}"

    @classmethod
    def from_tsv(cls, line: str) -> "SprintEntry":
        parts = line.strip().split("\t")
        if len(parts) != 5:
            raise ValueError(f"Invalid TSV line: {line}")
        return cls(sprint_id=parts[0], title=parts[1], status=parts[2], created_at=parts[3], updated_at=parts[4])


class SprintLedger:
    """Manages the sprint ledger TSV file."""

    HEADER = "sprint_id\ttitle\tstatus\tcreated_at\tupdated_at"

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

    def add(self, sprint_id: str, title: str, status: str = "planned") -> SprintEntry:
        sprint_id = str(int(sprint_id)).zfill(3)
        if sprint_id in self.entries:
            raise ValueError(f"Sprint {sprint_id} already exists")
        now = self._now()
        entry = SprintEntry(sprint_id=sprint_id, title=title, status=status, created_at=now, updated_at=now)
        self.entries[sprint_id] = entry
        return entry

    def update_status(self, sprint_id: str, status: str) -> SprintEntry:
        sprint_id = str(int(sprint_id)).zfill(3)
        if sprint_id not in self.entries:
            raise ValueError(f"Sprint {sprint_id} not found")
        if status not in SprintEntry.VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}. Must be one of {SprintEntry.VALID_STATUSES}")
        entry = self.entries[sprint_id]
        entry.status = status
        entry.updated_at = self._now()
        return entry

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
        pattern = re.compile(r"^# Sprint (\d+): (.+)$", re.MULTILINE)
        filename_pattern = re.compile(r"SPRINT-(\d+)\.md")
        for md_file in self.path.parent.glob("SPRINT-*.md"):
            match = filename_pattern.match(md_file.name)
            if not match:
                continue
            sprint_id = match.group(1).zfill(3)
            content = md_file.read_text(encoding="utf-8")
            title_match = pattern.search(content)
            title = title_match.group(2).strip() if title_match else f"Sprint {sprint_id}"
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
    """Resolve ledger.tsv relative to the current working directory (project root)."""
    return Path.cwd() / "docs" / "sprints" / "ledger.tsv"


def print_entry(entry: SprintEntry, verbose: bool = False) -> None:
    icons = {"planned": " ", "in_progress": "*", "completed": "+", "skipped": "-"}
    print(f"[{icons.get(entry.status, '?')}] {entry.sprint_id}: {entry.title}")
    if verbose:
        print(f"    Status: {entry.status}")
        print(f"    Doc: {entry.doc_path}")
        print(f"    Created: {entry.created_at}")
        print(f"    Updated: {entry.updated_at}")


def cmd_stats(ledger: SprintLedger) -> None:
    counts = ledger.count_by_status()
    print("Sprint Ledger Statistics")
    print("========================")
    print(f"Total sprints: {sum(counts.values())}")
    print()
    for status, count in counts.items():
        print(f"  {status}: {count}")
    current = ledger.get_in_progress()
    if current:
        print()
        print(f"Current: {current.sprint_id} - {current.title}")
    next_sprint = ledger.get_next_planned()
    if next_sprint:
        print(f"Next: {next_sprint.sprint_id} - {next_sprint.title}")


def cmd_current(ledger: SprintLedger) -> None:
    current = ledger.get_in_progress()
    if current:
        print_entry(current, verbose=True)
    else:
        print("No sprint currently in progress")


def cmd_next(ledger: SprintLedger) -> None:
    next_sprint = ledger.get_next_planned()
    if next_sprint:
        print_entry(next_sprint, verbose=True)
    else:
        print("No planned sprints")


def cmd_list(ledger: SprintLedger, status: Optional[str] = None) -> None:
    entries = ledger.get_by_status(status) if status else sorted(ledger.entries.values(), key=lambda e: e.sprint_number)
    if not entries:
        print("No sprints found")
        return
    for entry in entries:
        print_entry(entry)


def cmd_add(ledger: SprintLedger, sprint_id: str, title: str) -> None:
    entry = ledger.add(sprint_id, title)
    ledger.save()
    print(f"Added sprint {entry.sprint_id}: {entry.title}")


def cmd_start(ledger: SprintLedger, sprint_id: str) -> None:
    entry = ledger.update_status(sprint_id, "in_progress")
    ledger.save()
    print(f"Started sprint {entry.sprint_id}: {entry.title}")


def cmd_complete(ledger: SprintLedger, sprint_id: str) -> None:
    entry = ledger.update_status(sprint_id, "completed")
    ledger.save()
    print(f"Completed sprint {entry.sprint_id}: {entry.title}")


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


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    cmd = sys.argv[1]
    ledger = SprintLedger(get_ledger_path()).load()

    try:
        if cmd == "stats":
            cmd_stats(ledger)
        elif cmd == "current":
            cmd_current(ledger)
        elif cmd == "next":
            cmd_next(ledger)
        elif cmd == "list":
            status = None
            if "--status" in sys.argv:
                idx = sys.argv.index("--status")
                if idx + 1 < len(sys.argv):
                    status = sys.argv[idx + 1]
            cmd_list(ledger, status)
        elif cmd == "add":
            if len(sys.argv) < 4:
                print("Usage: ledger.py add <sprint_id> <title>")
                return 1
            cmd_add(ledger, sys.argv[2], " ".join(sys.argv[3:]))
        elif cmd == "start":
            if len(sys.argv) < 3:
                print("Usage: ledger.py start <sprint_id>")
                return 1
            cmd_start(ledger, sys.argv[2])
        elif cmd == "complete":
            if len(sys.argv) < 3:
                print("Usage: ledger.py complete <sprint_id>")
                return 1
            cmd_complete(ledger, sys.argv[2])
        elif cmd == "skip":
            if len(sys.argv) < 3:
                print("Usage: ledger.py skip <sprint_id>")
                return 1
            cmd_skip(ledger, sys.argv[2])
        elif cmd == "status":
            if len(sys.argv) < 4:
                print("Usage: ledger.py status <sprint_id> <status>")
                return 1
            cmd_status(ledger, sys.argv[2], sys.argv[3])
        elif cmd == "sync":
            cmd_sync(ledger)
        else:
            print(f"Unknown command: {cmd}")
            print(__doc__)
            return 1
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
