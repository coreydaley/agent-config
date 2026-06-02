---
name: plane-init
description: >-
  Bootstrap a Plane-shaped markdown workspace + project under
  ~/Reports/<org>/<repo>/. Creates WORKSPACE.md (one per org) and
  PROJECT.md (one per repo) with sensible defaults derived from the
  upstream/origin git remote. Idempotent — re-running on an
  already-initialized project prints status and exits clean. Other
  plane-* skills (plane-audit-ingest, plane-audit-promote, plane-cycle-*)
  assume this has run.
argument-hint: "[scope-path] [--help]"
disable-model-invocation: true
---

# plane-init — bootstrap Plane-shaped reports

Creates the workspace + project metadata files under
`~/Reports/<org>/<repo>/` so the rest of the `plane-*` skills have a
place to write. The Plane data model (Workspace > Project > Work Item /
Cycle / Module / Epic / Milestone / Page) is mirrored to markdown files
with YAML frontmatter so a future migration to a Plane instance is
mechanical.

## Help mode

If the arguments include `--help` or `-h`, print the blurb below
verbatim and stop.

```
/plane-init — bootstrap Plane-shaped markdown reports

When to use it
  Once per project, before running any other plane-* skill.
  Re-running is safe — it never overwrites existing files.

What it does
  1. Resolves <org>/<repo> from the project's upstream (or origin)
     git remote. Falls back to local/<basename> for non-git dirs.
  2. Ensures ~/Reports/<org>/<repo>/ + standard subdirs exist
     (work-items/, cycles/, modules/, epics/, milestones/, pages/).
  3. Writes ~/Reports/<org>/WORKSPACE.md if missing.
  4. Writes ~/Reports/<org>/<repo>/PROJECT.md if missing.
  5. Prints the resulting paths.

Usage
  /plane-init [<scope-path>] [--help]

  <scope-path>  Path to the project root. Defaults to cwd.
  --help, -h    Print this help.
```

## What to do

1. **Parse args.** If `--help` / `-h` present, print the help blurb
   above and stop.

2. **Run the init script:**

   ```bash
   python3 scripts/init.py [SCOPE_PATH]
   ```

   The script:
   - Resolves `<org>/<repo>` (via `lib/plane-runner.sh resolve`).
   - Creates `~/Reports/<org>/<repo>/` + subdirs.
   - Writes `WORKSPACE.md` if missing — defaults `name = <org>`.
   - Writes `PROJECT.md` if missing — defaults `name = <repo>` titled,
     `repo_url` set from the resolved remote.
   - Prints a status line per created / already-present file.

3. **Report.** Echo the script's status output verbatim and stop.

## Artifacts

```
~/Reports/<org>/                       <- workspace dir
  WORKSPACE.md
  <repo>/                              <- project dir
    PROJECT.md
    work-items/                        <- empty until plane-audit-ingest or manual work-item creation
    cycles/
    modules/
    epics/
    milestones/
    pages/
    audits/                            <- existing; unchanged
```

## Don'ts

- **Don't** overwrite an existing WORKSPACE.md or PROJECT.md. If the
  user wants to edit, they edit directly.
- **Don't** create work items, cycles, modules, etc. — those are
  produced by their own skills.
- **Don't** touch anything under `audits/` — that layout is owned by
  the audit-* skills and existing tooling.

## ARGUMENTS

Optional scope path, defaulting to cwd. `--help` / `-h` prints help.

The literal arguments passed by the user follow:

$ARGUMENTS
