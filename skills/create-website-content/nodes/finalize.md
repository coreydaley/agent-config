# Node: finalize (Claude)

Apply the fact-check and put the page into the site. The only node that
writes into the repo.

## Steps

1. **Write the page** at the target path, applying every accepted fix. For a
   landing section, edit `landing.sections` in the app's `_index.md`.
   - Answer pages go live today: `date:` today, no `draft`. If the user wants
     it held, `draft: true`.
   - Pages describing unreleased app behavior can still publish, with the
     `since` note.

2. **Link it in:**
   - A "won't open" or format question gets a row in the hub table on
     `content/apps/purrchiver/archive-wont-open-mac.md` (or the app's
     equivalent).
   - Help pages that cover the same ground (`help/other-tools.md`,
     `help/troubleshooting.md`, …) link here instead of repeating weaker
     advice. Update any of their statements this research proved wrong.

3. **Build-check:**
   ```bash
   B="$(mktemp -d)"; hugo --quiet -d "$B" && test -f "$B/<page path>/index.html"
   ```
   Every internal link on the page must resolve in `$B`. Delete `$B`.

## Outgoing edge

```bash
scripts/walk.sh transition --state "$STATE" --from finalize --to visual_check
```
