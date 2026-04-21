#!/usr/bin/env python3
"""
Sprint Manager - CLI tool for tracking sprint progress.

Usage:
    python3 sprints.py --stats                        # Show overview
    python3 sprints.py --current                      # Show in_progress sprint
    python3 sprints.py --next                         # Show next planned sprint
    python3 sprints.py --add 003 "Sprint Title"       # Add new sprint
    python3 sprints.py --start 001                    # Mark as in_progress
    python3 sprints.py --complete 001                 # Mark as completed
    python3 sprints.py --skip 001                     # Mark as skipped
    python3 sprints.py --set-status 001 completed     # Set arbitrary status
    python3 sprints.py --list [--status planned]     # List sprints
    python3 sprints.py --sync                         # Sync from .md files

Data model and display helpers are imported from ~/.claude/lib/sprint_ledger.py
so other scripts (e.g. the commit planner) can share the same schema without
duplicating TSV parsing logic.
"""

import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path.home() / ".claude" / "lib"))

from sprint_ledger import (  # noqa: E402
    SprintEntry,
    SprintLedger,
    get_ledger_path,
    _symbol,
    _bold_pad,
    _relative_compact,
    _relative_phrase,
    _absolute_date,
    _format_duration,
    _format_duration_compact,
    _effective_timestamp,
    _WHEN_LABELS,
)


def print_verbose(entry: SprintEntry) -> None:
    """Render a single entry as a block with aligned key/value rows."""
    status_label = entry.status.replace("_", " ")
    when_label = _WHEN_LABELS.get(entry.status, "Updated")
    ts = _effective_timestamp(entry)
    print(f"{_symbol(entry.status)} Sprint {entry.sprint_id}  {entry.title}")
    print()
    print(f"  {'Status':<12} {status_label}")
    print(f"  {when_label:<12} {_relative_phrase(ts)}  ({_absolute_date(ts)})")
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
    if entry.participants:
        print(f"  {'Participants':<12} {entry.participants}")
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

    header_parts = [
        f"{_symbol(s)} {counts[s]}"
        for s in ("completed", "in_progress", "planned", "skipped")
        if counts.get(s, 0) > 0
    ]
    print(f"{total} sprint{'s' if total != 1 else ''}  " + "   ".join(header_parts))
    print()

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
    ledger: SprintLedger, sprint_id: str, title: str,
    recommended_model: str = "", participants: str = "",
) -> None:
    entry = ledger.add(
        sprint_id, title,
        recommended_model=recommended_model,
        participants=participants,
    )
    ledger.save()
    extras = []
    if entry.recommended_model:
        extras.append(f"recommended: {entry.recommended_model}")
    if entry.participants:
        extras.append(f"participants: {entry.participants}")
    suffix = f" ({', '.join(extras)})" if extras else ""
    print(f"Added sprint {entry.sprint_id}: {entry.title}{suffix}")


def cmd_set_fit(ledger: SprintLedger, sprint_id: str, fit: str) -> None:
    entry = ledger.set_fit(sprint_id, fit)
    ledger.save()
    print(f"Set fit for sprint {entry.sprint_id}: {entry.fit.replace('_', ' ')}")


def cmd_set_participants(ledger: SprintLedger, sprint_id: str, participants: str) -> None:
    entry = ledger.set_participants(sprint_id, participants)
    ledger.save()
    display = entry.participants or "(none)"
    print(f"Set participants for sprint {entry.sprint_id}: {display}")


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

    with_rec = [e for e in records if e.recommended_model and e.model]
    if with_rec:
        matches = sum(1 for e in with_rec if e.recommended_model == e.model)
        pct = (matches / len(with_rec)) * 100
        print(
            f"  {'Rec match':<10} {matches}/{len(with_rec)} "
            f"({pct:.0f}% accepted recommendation)"
        )

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


HELP_TEXT = """\
/sprints — manage the sprint record

Usage:
  /sprints <flag> [args]

Action flags (mutually exclusive):
  --stats                              Show overview of all sprints
  --current                            Show the in-progress sprint
  --next                               Show the next planned sprint
  --list                               List all sprints (combine with --status to filter)
  --velocity                           Velocity statistics across completed sprints
  --add NNN "Title"                    Add a new sprint entry
                                         (optional --recommended-model=<n>, --participants=<list>)
  --start NNN [--model=<n>]            Mark sprint NNN as in_progress; record model if given
  --complete NNN [--model=<n>]         Mark sprint NNN as completed
  --skip NNN                           Mark sprint NNN as skipped
  --set-status NNN <status>            Set arbitrary status for sprint NNN
  --set-fit NNN <verdict>              Record post-sprint fit (over_powered /
                                         right_sized / under_powered) from the retro
  --set-participants NNN <list>        Replace participants list for sprint NNN
                                         (comma-separated subset of: claude, codex)
  --sync                               Sync from *-sprint-plan-SPRINT-*.md files
  --help, -h                           Show this help and exit

Modifier flags:
  --status=<status>                    Filter for --list (e.g. --list --status=planned)
  --model=<n>                          Record the model (opus/sonnet/haiku) for a sprint.
                                         Pairs with --start (primary) or --complete.
  --recommended-model=<n>              What sprint-plan suggested at planning time.
                                         Pairs with --add.
  --participants=<list>                Who participated in planning this sprint.
                                         Comma-separated subset of: claude, codex.
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
    # extracting modifier flags.
    positional: list[str] = []
    status_filter: Optional[str] = None
    model_modifier: Optional[str] = None
    recommended_model_modifier: Optional[str] = None
    participants_modifier: Optional[str] = None
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
        elif arg.startswith("--participants="):
            participants_modifier = arg.split("=", 1)[1]
        elif arg == "--participants" and i + 1 < len(sys.argv):
            participants_modifier = sys.argv[i + 1]
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
                    "[--recommended-model=<n>] [--participants=<list>]"
                )
                return 1
            cmd_add(
                ledger, positional[0], " ".join(positional[1:]),
                recommended_model_modifier or "",
                participants_modifier or "",
            )
        elif flag == "--start":
            if not positional:
                print("Usage: sprints.py --start <sprint_id> [--model=<n>]")
                return 1
            cmd_start(ledger, positional[0], model_modifier)
        elif flag == "--complete":
            if not positional:
                print("Usage: sprints.py --complete <sprint_id> [--model=<n>]")
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
        elif flag == "--set-participants":
            if len(positional) < 2:
                print("Usage: sprints.py --set-participants <sprint_id> <comma-separated list>")
                return 1
            cmd_set_participants(ledger, positional[0], positional[1])
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
