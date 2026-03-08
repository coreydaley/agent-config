# Sprint Planning Reference

## Directory Layout

```
docs/sprints/
├── README.md              # This file
├── ledger.tsv             # Sprint status ledger (managed via /ledger skill)
├── SPRINT-001.md          # Completed sprints
├── SPRINT-002.md
├── ...
└── drafts/
    ├── SPRINT-NNN-INTENT.md
    ├── SPRINT-NNN-CLAUDE-DRAFT.md
    ├── SPRINT-NNN-CODEX-DRAFT.md
    ├── SPRINT-NNN-CLAUDE-DRAFT-CODEX-CRITIQUE.md
    ├── SPRINT-NNN-MERGE-NOTES.md
    ├── SPRINT-NNN-DEVILS-ADVOCATE.md
    └── SPRINT-NNN-SECURITY-REVIEW.md
```

## Naming Convention

Sprint documents are named `SPRINT-NNN.md` where `NNN` is zero-padded to 3 digits (e.g., `SPRINT-001.md`, `SPRINT-042.md`).

Draft artifacts live in `drafts/` and follow the same `NNN` prefix.

## Ledger

Sprint status is tracked in `ledger.tsv`. Manage it via the `/ledger` skill:

| Subcommand | Effect |
|---|---|
| `/ledger stats` | Overview of all sprints |
| `/ledger add NNN "Title"` | Register a new sprint |
| `/ledger start NNN` | Mark sprint in_progress |
| `/ledger complete NNN` | Mark sprint completed |
| `/ledger sync` | Sync ledger from SPRINT-*.md files |

## Standard Sprint Template

```markdown
# Sprint NNN: [Title]

## Overview

2-3 paragraphs on the "why" and high-level approach.

## Use Cases

1. **Use case name**: Description
2. ...

## Architecture

Diagrams (ASCII art), component descriptions, data flow.

## Implementation Plan

### Phase 1: [Name] (~X%)

**Files:**
- `path/to/file.ext` - Description

**Tasks:**
- [ ] Task 1
- [ ] Task 2

### Phase 2: ...

## Files Summary

| File | Action | Purpose |
|------|--------|---------|
| `path/to/file` | Create/Modify | Description |

## Definition of Done

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Tests pass

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| ... | ... | ... | ... |

## Security Considerations

- Item 1

## Dependencies

- Sprint NNN (if any)

## Open Questions

Uncertainties needing resolution.
```
