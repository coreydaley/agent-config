#!/usr/bin/env python3
"""
Sprint Manager — CLI tool for tracking sprint progress.

Sprints are keyed by session timestamp (e.g. "2026-05-01T14-30-00"),
which corresponds to the folder name under ~/Reports/<org>/<repo>/sprints/.
Most commands accept a session timestamp, a session prefix (e.g.
"2026-05-01"), or a title substring — fuzzy lookups are resolved
to a single entry, with an error if the query is ambiguous.

Usage:
    python3 sprints.py --stats                      # Show overview
    python3 sprints.py --current                    # Show in-progress sprint
    python3 sprints.py --next                       # Show next planned sprint
    python3 sprints.py --add <TS> "Title"           # Register an existing session
    python3 sprints.py --start <query>              # Mark as in_progress
    python3 sprints.py --complete <query>           # Mark as completed
    python3 sprints.py --skip <query>               # Mark as skipped
    python3 sprints.py --set-status <query> <status>
    python3 sprints.py --list [--status planned]
    python3 sprints.py --sync                       # Sync from sprints/<TS>/SPRINT.md
    python3 sprints.py --path <query>               # Print absolute session folder path

Data model and display helpers are imported from ~/.claude/lib/sprint_ledger.py.
"""

import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path.home() / ".claude" / "lib"))

from sprint_ledger import (  # noqa: E402
    SprintEntry,
    SprintLedger,
    get_ledger_path,
    get_sprints_dir,
    _symbol,
    _bold_pad,
    _relative_compact,
    _relative_phrase,
    _absolute_date,
    _format_duration,
    _format_duration_compact,
    _effective_timestamp,
    _short_session,
    _WHEN_LABELS,
)


def _resolve(ledger: SprintLedger, query: str) -> SprintEntry:
    """Resolve a user-supplied query to exactly one entry. Errors on
    ambiguity or no-match."""
    matches = ledger.find(query)
    if not matches:
        raise ValueError(f"No sprint matching: {query!r}")
    if len(matches) > 1:
        lines = [f"  {e.session}  {e.title}" for e in matches]
        raise ValueError(
            f"Ambiguous query {query!r} — {len(matches)} matches:\n"
            + "\n".join(lines)
            + "\nUse a more specific session timestamp or title fragment."
        )
    return matches[0]


def print_verbose(entry: SprintEntry) -> None:
    """Render a single entry as a block with aligned key/value rows."""
    status_label = entry.status.replace("_", " ")
    when_label = _WHEN_LABELS.get(entry.status, "Updated")
    ts = _effective_timestamp(entry)
    print(f"{_symbol(entry.status)} {entry.session}  {entry.title}")
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
            f"{current.title}   (started {since}{model_note})"
        )
    if next_sprint:
        print(
            f"  {_bold_pad('Next', 9)}{_symbol(next_sprint.status)} "
            f"{next_sprint.title}"
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
            f"{next_sprint.session}  {next_sprint.title}."
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
        else sorted(ledger.entries.values(), key=lambda e: e.session)
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
        sess = _short_session(entry.session)
        if right:
            padded = entry.title.ljust(max_title)
            print(f"  {_symbol(entry.status)} {sess}  {padded}   {right}")
        else:
            print(f"  {_symbol(entry.status)} {sess}  {entry.title}")


def cmd_add(
    ledger: SprintLedger, session: str, title: str,
    recommended_model: str = "", participants: str = "",
) -> None:
    entry = ledger.add(
        session, title,
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
    print(f"Registered: {entry.session}  {entry.title}{suffix}")


def cmd_set_fit(ledger: SprintLedger, query: str, fit: str) -> None:
    entry = _resolve(ledger, query)
    ledger.set_fit(entry.session, fit)
    ledger.save()
    print(f"Set fit for {entry.session} ({entry.title}): {fit.replace('_', ' ')}")


def cmd_set_participants(ledger: SprintLedger, query: str, participants: str) -> None:
    entry = _resolve(ledger, query)
    ledger.set_participants(entry.session, participants)
    display = entry.participants or "(none)"
    ledger.save()
    print(f"Set participants for {entry.session} ({entry.title}): {display}")


def cmd_start(ledger: SprintLedger, query: str, model: Optional[str] = None) -> None:
    entry = _resolve(ledger, query)
    ledger.update_status(entry.session, "in_progress", model)
    ledger.save()
    model_note = f" ({entry.model})" if entry.model else ""
    print(f"Started: {entry.session}  {entry.title}{model_note}")


def cmd_complete(ledger: SprintLedger, query: str, model: Optional[str] = None) -> None:
    entry = _resolve(ledger, query)
    ledger.update_status(entry.session, "completed", model)
    ledger.save()
    duration_note = (
        f" in {_format_duration(entry.duration_seconds)}"
        if entry.duration_seconds is not None
        else ""
    )
    print(f"Completed: {entry.session}  {entry.title}{duration_note}")


def cmd_skip(ledger: SprintLedger, query: str) -> None:
    entry = _resolve(ledger, query)
    ledger.update_status(entry.session, "skipped")
    ledger.save()
    print(f"Skipped: {entry.session}  {entry.title}")


def cmd_status(ledger: SprintLedger, query: str, status: str) -> None:
    entry = _resolve(ledger, query)
    ledger.update_status(entry.session, status)
    ledger.save()
    print(f"Updated {entry.session} to {entry.status}")


def cmd_path(ledger: SprintLedger, query: str) -> None:
    """Print the absolute session folder path for the resolved entry."""
    entry = _resolve(ledger, query)
    print(get_sprints_dir() / entry.session)


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
/sprints — manage the sprint ledger

Sprints are identified by their session timestamp (e.g.
"2026-05-01T14-30-00"). Most commands accept a fuzzy query: a session
prefix or a title substring. Ambiguous queries error out with the
matching list.

Usage:
  /sprints <flag> [args]

Action flags (mutually exclusive):
  --stats                              Show overview of all sprints
  --current                            Show the in-progress sprint
  --next                               Show the next planned sprint
  --list                               List all sprints (combine with --status to filter)
  --velocity                           Velocity statistics across completed sprints
  --add <TS> "Title"                   Register an existing session
                                         (optional --recommended-model=<n>, --participants=<list>)
  --start <query> [--model=<n>]        Mark sprint as in_progress; record model if given
  --complete <query> [--model=<n>]     Mark sprint as completed
  --skip <query>                       Mark sprint as skipped
  --set-status <query> <status>        Set arbitrary status
  --set-fit <query> <verdict>          Record post-sprint fit (over_powered /
                                         right_sized / under_powered) from the retro
  --set-participants <query> <list>    Replace participants list
                                         (comma-separated subset of: claude, codex)
  --sync                               Sync from sprints/<TS>/SPRINT.md files
  --path <query>                       Print absolute session folder path
  --help, -h                           Show this help and exit

Modifier flags:
  --status=<status>                    Filter for --list (e.g. --list --status=planned)
  --model=<n>                          Record model (opus/sonnet/haiku) on a sprint.
                                         Pairs with --start (primary) or --complete.
  --recommended-model=<n>              What sprint-plan suggested at planning time.
                                         Pairs with --add.
  --participants=<list>                Who participated in planning (claude, codex).
                                         Pairs with --add.

Valid statuses: planned, in_progress, completed, skipped

Ledger: ~/Reports/<org>/<repo>/ledger.tsv (org/repo from `git remote get-url origin`)
Sprint sessions: ~/Reports/<org>/<repo>/sprints/<TS>/

Full documentation: ~/.claude/skills/sprints/SKILL.md"""


def main() -> int:
    if len(sys.argv) < 2:
        print(HELP_TEXT)
        return 1

    if sys.argv[1] in ("--help", "-h", "help"):
        print(HELP_TEXT)
        return 0

    flag = sys.argv[1]
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
                    "Usage: sprints.py --add <session-TS> <title> "
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
                print("Usage: sprints.py --start <query> [--model=<n>]")
                return 1
            cmd_start(ledger, positional[0], model_modifier)
        elif flag == "--complete":
            if not positional:
                print("Usage: sprints.py --complete <query> [--model=<n>]")
                return 1
            cmd_complete(ledger, positional[0], model_modifier)
        elif flag == "--skip":
            if not positional:
                print("Usage: sprints.py --skip <query>")
                return 1
            cmd_skip(ledger, positional[0])
        elif flag == "--set-status":
            if len(positional) < 2:
                print("Usage: sprints.py --set-status <query> <status>")
                return 1
            cmd_status(ledger, positional[0], positional[1])
        elif flag == "--set-fit":
            if len(positional) < 2:
                print("Usage: sprints.py --set-fit <query> <over_powered|right_sized|under_powered>")
                return 1
            cmd_set_fit(ledger, positional[0], positional[1])
        elif flag == "--set-participants":
            if len(positional) < 2:
                print("Usage: sprints.py --set-participants <query> <comma-separated list>")
                return 1
            cmd_set_participants(ledger, positional[0], positional[1])
        elif flag == "--path":
            if not positional:
                print("Usage: sprints.py --path <query>")
                return 1
            cmd_path(ledger, positional[0])
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
