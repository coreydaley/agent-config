# Node: draft-pr-body

Write the PR title and body from PLAN.md and the actual commits. The body is outbound prose, so it's drafted to a file and shown before anything is created. On re-entry from `ask-open` (`user_edit`), apply the user's changes and re-draft.

## Inputs

- `plan_path`, `worktree`, `base_ref`, `source_id`, `gaps`, `pr_number` from walker state
- PLAN.md: title, Problem, Approach, Files, Tests, Scope Out, Follow-ups
- The user's edit request, when re-entered

```bash
STATE="$PLAN_DIR/.walk-state.build.json"
```

## Steps

1. **Title.** Per the template in `lib/pr-artifacts.md`: a Conventional Commits subject, `<type>(<scope>): <summary>`, imperative, lowercase, at most 72 characters. No issue number in the title (it goes in Linked), never a feature (parent) issue number.

2. **Body.** Written for a reviewer who has the PR and the linked issue and nothing else. Use the PR body template in `lib/pr-artifacts.md` (Summary, Changes, Testing, Not in this PR, Linked) and the prose rules in `lib/code-hygiene.md`. "Not in this PR" carries Scope Out items a reviewer will ask about and any ship-with gaps from verify. Linked is `Closes #N` when `source_id` is a GitHub issue, omitted otherwise. Omit sections with nothing to say.

3. **Existing PR** (`pr_number` set): the body is a *replacement* for the current one, reflecting the branch as it is now. Fetch the current body first so nothing a human added (a reviewer checklist, a deployment note) is lost. Carry those over.

4. **Re-entry from `user_edit`.** Apply exactly what the user asked to change. Don't re-derive the rest.

5. **Write `$PLAN_DIR/pr-body.md`** with the title on the first line as `# <title>` and the body beneath.

## Outputs

- `$PLAN_DIR/pr-body.md`

## Outgoing edges

- → `display` (always, single outgoing edge)

```bash
scripts/walk.sh transition --state "$STATE" --from draft_pr_body --to display
```

## Notes

- **The body describes the branch, not the plan.** If verify shipped with a gap, the body says so. If a task was dropped during implement, it isn't listed under Changes.
- **Short beats complete.** A reviewer reads the body once. Everything they need to start reading the diff, nothing they'll re-derive from it anyway.
