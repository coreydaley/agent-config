#!/usr/bin/env python3
"""Scaffold a new audit-* skill from an existing skill as template.

Copies the source skill's directory tree to a new slug, substituting
the audit-name token everywhere it appears (graph.dot digraph name,
validate.py docstring, init.md `audit-runner.sh init` arg, etc.).
Leaves content-heavy files (SKILL.md, orient.md, independent-reviews.md,
report.md, synthesis.md, handoff.md, prompts/*) as stubs that need
manual editing.

Usage:
    scaffold-audit-skill.py <source-slug> <target-slug> <display-name>

Example:
    scaffold-audit-skill.py audit-apple-design audit-apple-build-release "Apple Build & Release"

The script is idempotent only in the sense that it refuses to overwrite
an existing target dir. Delete the target dir manually if you want to
re-run.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"


def slug_to_audit_name(slug: str) -> str:
    """`audit-apple-build-release` -> `apple-build-release`."""
    return slug.removeprefix("audit-")


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(__doc__, file=sys.stderr)
        return 2
    src_slug, dst_slug, dst_display = argv[1], argv[2], argv[3]
    src_dir = SKILLS / src_slug
    dst_dir = SKILLS / dst_slug
    if not src_dir.is_dir():
        print(f"source skill not found: {src_dir}", file=sys.stderr)
        return 1
    if dst_dir.exists():
        print(f"target already exists; refusing to overwrite: {dst_dir}", file=sys.stderr)
        return 1

    src_audit = slug_to_audit_name(src_slug)
    dst_audit = slug_to_audit_name(dst_slug)
    # `audit_apple_design` <-> `audit_apple_build_release` (digraph identifier)
    src_id = src_slug.replace("-", "_")
    dst_id = dst_slug.replace("-", "_")
    # Display strings to swap. We try to be conservative: only token-level
    # replacements, not whole-prose rewrites. The display string in headings
    # is the human-readable form ("Apple Design" -> "Apple Build & Release").
    src_display_guess = " ".join(w.capitalize() for w in src_audit.split("-"))

    shutil.copytree(src_dir, dst_dir)

    for path in dst_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.name == "graph.svg":
            # Will be re-rendered.
            path.unlink()
            continue
        text = path.read_text()
        # Order matters: replace the most specific (digraph id) before the
        # less specific (audit slug), to avoid `audit_apple_design` getting
        # half-rewritten by the slug substitution.
        new = text
        new = new.replace(src_id, dst_id)
        new = new.replace(src_slug, dst_slug)
        new = new.replace(src_audit, dst_audit)
        new = new.replace(src_display_guess, dst_display)
        if new != text:
            path.write_text(new)

    # Drop a SCAFFOLD-TODO breadcrumb listing the files that need manual
    # content authorship. The reviewer can delete this file once those are
    # filled in.
    todo = dst_dir / "SCAFFOLD-TODO.md"
    todo.write_text(
        f"""# Scaffold TODO — {dst_slug}

This skill was scaffolded from `{src_slug}` via
`scripts/scaffold-audit-skill.py`. The boilerplate (graph.dot, walker
wrapper, validate.py, init/verify/handoff/escalate/terminal/ingest
nodes, emergency-exit stub, devils-advocate node) is in place and
should not need manual edits beyond audit-name substitution (already
done).

The following files contain audit-specific content that needs to be
authored fresh for this audit (the scaffold copied the source skill's
text verbatim, which is wrong for a different audit):

- [ ] `SKILL.md` — frontmatter `description:`, the embedded help blurb,
      the "Don'ts" section, any cross-references to sibling skills.
- [ ] `nodes/orient.md` — Phase 1 tooling (if any) and survey checklist.
- [ ] `nodes/independent-reviews.md` — Claude's review checklist
      (categories, schema, severity anchors). The single source of truth
      for the review categories lives in `prompts/codex-review.md`;
      mirror it here.
- [ ] `nodes/synthesis.md` — the audit-specific compound-finding patterns
      block, and the four-factor severity recalibration list.
- [ ] `nodes/report.md` — sprint-mapping override table, per-task fields,
      report template, Definition of Done.
- [ ] `nodes/handoff.md` — audit-specific warnings block.
- [ ] `prompts/codex-review.md` — the codex review prompt body. This is
      where the categories list lives canonically; mirror in
      independent-reviews.md.
- [ ] `prompts/codex-devils-advocate.md` — audit-specific false-positive
      and missing-finding categories.

After editing, regenerate the graph and validate:

```sh
bash scripts/render.sh
python3 scripts/validate.py
```

Then delete this file.
""",
    )

    print(f"Scaffolded {dst_slug} from {src_slug}.")
    print(f"  Audit name token: {src_audit} -> {dst_audit}")
    print(f"  Digraph id      : {src_id} -> {dst_id}")
    print(f"  Display heuristic: '{src_display_guess}' -> '{dst_display}'")
    print(f"  See {dst_dir}/SCAFFOLD-TODO.md for next steps.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
