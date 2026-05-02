#!/usr/bin/env python3
"""
Commit Planner - build a structured commit plan from the git working tree.

Analyzes uncommitted changes and groups them for atomic commits. Pre-staged
files form one group; everything else is flagged as "unclassified" for the
agent to group by logical purpose. Sprint artifacts are no longer specially
detected — current sprints live outside the repo (~/Reports/...) so they
never appear in `git status` anyway.

Usage:
    python3 commit.py              # Emit JSON plan to stdout
    python3 commit.py --dry        # Emit human-readable plan, no side effects
    python3 commit.py --help

The script itself never commits, stages, or mutates anything. It reads
git state and the sprint ledger, then outputs a plan. The calling agent
(global /commit skill) reads the plan, fills in conventional commit
types/scopes/summaries for unclassified groups, and performs the git
operations.

Exit codes:
    0  success
    1  user error (bad args, unknown flag)
    2  git not available / not a git repo
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path.home() / ".claude" / "lib"))

from sprint_ledger import (  # noqa: E402
    _C,
    _colorize,
    _use_color,
)


# --- Agent identities -----------------------------------------------

AGENT_TRAILERS = {
    "claude": "Co-authored-by: Claude <noreply@anthropic.com>",
    "codex": "Co-authored-by: Codex <noreply@openai.com>",
}


# --- Git plumbing ---------------------------------------------------

def _run_git(*args: str) -> tuple[int, str, str]:
    """Run git with the given args; return (returncode, stdout, stderr).
    All output decoded as utf-8, stripped of trailing whitespace."""
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except FileNotFoundError:
        return 127, "", "git executable not found"
    return result.returncode, result.stdout.rstrip(), result.stderr.rstrip()


def _in_git_repo() -> bool:
    rc, _, _ = _run_git("rev-parse", "--is-inside-work-tree")
    return rc == 0


def _current_branch() -> str:
    rc, out, _ = _run_git("branch", "--show-current")
    return out if rc == 0 else ""


TICKET_PATTERN = re.compile(r"^([A-Z]+-\d+)")


def _extract_ticket_id(branch: str) -> Optional[str]:
    """Pull a ticket ID like ENG-1234 off the start of a branch name."""
    m = TICKET_PATTERN.match(branch)
    return m.group(1) if m else None


def _discover_changes() -> dict:
    """Discover all uncommitted changes. Returns dict with:
        staged: list of file paths already staged
        modified: list of modified-but-unstaged paths (includes deletions)
        untracked: list of untracked paths (excluding .gitignore matches)
    """
    staged: list[str] = []
    modified: list[str] = []
    untracked: list[str] = []

    # porcelain=v1 gives us stable two-char status codes per line:
    #   XY path
    #   X = staged status, Y = unstaged status
    rc, out, err = _run_git("status", "--porcelain=v1", "--untracked-files=all")
    if rc != 0:
        return {"staged": staged, "modified": modified, "untracked": untracked, "error": err}

    for line in out.splitlines():
        if not line:
            continue
        # Format: "XY path" where XY is exactly 2 chars followed by space
        if len(line) < 3:
            continue
        x, y = line[0], line[1]
        path = line[3:]
        # Rename format is "old -> new"; take the new path for both sides.
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        # Strip surrounding quotes git adds for paths with special chars.
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1]

        if x == "?" and y == "?":
            untracked.append(path)
        else:
            if x != " " and x != "?":
                staged.append(path)
            if y != " " and y != "?":
                modified.append(path)

    return {"staged": staged, "modified": modified, "untracked": untracked}


# --- Trailer helpers ------------------------------------------------

def _default_trailers() -> list[str]:
    """Default Co-authored-by trailer set: just Claude."""
    return [AGENT_TRAILERS["claude"]]


# --- Plan assembly --------------------------------------------------

def _build_plan() -> dict:
    """Read git state, return a structured commit plan.

    Plan shape:
        {
            "ticket_id": "ENG-742" or None,
            "branch": "<current branch>",
            "warnings": [str, ...],
            "groups": [
                {
                    "kind": "pre-staged" | "unclassified",
                    "label": "<short label for this group>",
                    "files": [str, ...],
                    "trailers": [str, ...],    # Co-authored-by lines
                    "needs_agent_decision": [str, ...],  # what agent must fill in
                },
                ...
            ],
            "commit_order": [label, ...],   # order in which groups should be committed
        }
    """
    changes = _discover_changes()
    warnings: list[str] = []
    if "error" in changes:
        warnings.append(f"git status returned error: {changes['error']}")

    branch = _current_branch()
    ticket = _extract_ticket_id(branch)

    staged = changes["staged"]
    modified = changes["modified"]
    untracked = changes["untracked"]

    # Files that are staged should only appear in staged, even if also modified.
    unstaged_candidates = list(dict.fromkeys(modified + untracked))
    unstaged_candidates = [f for f in unstaged_candidates if f not in set(staged)]

    groups: list[dict] = []

    # Group 1: pre-staged (always first if non-empty)
    if staged:
        groups.append({
            "kind": "pre-staged",
            "label": "pre-staged",
            "files": sorted(staged),
            "trailers": _default_trailers(),
            "needs_agent_decision": ["type", "scope", "summary", "body"],
        })

    # Group 2: unclassified (everything else, if any)
    if unstaged_candidates:
        groups.append({
            "kind": "unclassified",
            "label": "unclassified",
            "files": sorted(unstaged_candidates),
            "trailers": _default_trailers(),
            "needs_agent_decision": ["grouping", "type", "scope", "summary", "body"],
        })

    order = [g["label"] for g in groups]

    return {
        "ticket_id": ticket,
        "branch": branch,
        "warnings": warnings,
        "groups": groups,
        "commit_order": order,
    }


# --- Dry-run rendering ----------------------------------------------

def _render_dry(plan: dict) -> str:
    """Human-readable rendering for --dry. No JSON, no machine output."""
    lines: list[str] = []
    use_color = _use_color()

    def header(text: str) -> str:
        return _colorize(text, _C.BOLD) if use_color else text

    def muted(text: str) -> str:
        return _colorize(text, _C.DIM) if use_color else text

    lines.append(header("Commit Plan"))
    lines.append("")
    lines.append(f"  Branch:     {plan['branch'] or '(detached)'}")
    if plan["ticket_id"]:
        lines.append(f"  Ticket:     {plan['ticket_id']}")
    lines.append(f"  Groups:     {len(plan['groups'])}")
    lines.append("")

    if plan["warnings"]:
        lines.append(header("Warnings"))
        for w in plan["warnings"]:
            lines.append(f"  ! {w}")
        lines.append("")

    if not plan["groups"]:
        lines.append(muted("  (no changes to commit)"))
        return "\n".join(lines)

    for i, g in enumerate(plan["groups"], start=1):
        kind_label = g["kind"]
        lines.append(header(f"  [{i}] {kind_label}  ({len(g['files'])} file{'s' if len(g['files']) != 1 else ''})"))
        for f in g["files"]:
            lines.append(f"      {f}")
        lines.append("")
        lines.append(f"      Trailers:")
        for t in g["trailers"]:
            lines.append(f"        {t}")
        if plan["ticket_id"]:
            lines.append(f"        Addresses {plan['ticket_id']}")
        lines.append(f"      Agent must decide: {', '.join(g['needs_agent_decision'])}")
        lines.append("")

    lines.append(muted("Dry run — no commits made."))
    return "\n".join(lines)


# --- CLI entry point ------------------------------------------------

HELP_TEXT = """\
commit.py — build a structured commit plan from the git working tree

Usage:
  python3 commit.py              Emit JSON commit plan to stdout
  python3 commit.py --dry        Emit human-readable plan (no side effects)
  python3 commit.py --help       Show this help and exit

This script NEVER commits, stages, or mutates state. It only reads
git state and outputs a plan describing how changes should be
grouped for atomic commits.

The JSON output shape is documented in the module docstring at the
top of this file. Groups are:
  pre-staged        — files already in the index (committed first)
  unclassified      — everything else (agent must group by purpose)

All groups default to a single Claude Co-authored-by trailer.

Full documentation: ~/.claude/skills/commit/SKILL.md"""


def main() -> int:
    args = sys.argv[1:]

    if args and args[0] in ("--help", "-h", "help"):
        print(HELP_TEXT)
        return 0

    dry = False
    unknown: list[str] = []
    for a in args:
        if a == "--dry":
            dry = True
        else:
            unknown.append(a)

    if unknown:
        print(f"Unknown flag(s): {' '.join(unknown)}", file=sys.stderr)
        print(HELP_TEXT, file=sys.stderr)
        return 1

    if not _in_git_repo():
        print("Not inside a git repository.", file=sys.stderr)
        return 2

    plan = _build_plan()

    if dry:
        print(_render_dry(plan))
    else:
        print(json.dumps(plan, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
