# Node: visual-check (Claude)

Look at the page the way readers will, on the local server.

## Steps

1. Use the running `hugo server -D -F` on port 1313 if there is one; otherwise
   start one in the background and stop it afterwards.
2. In Chrome (claude-in-chrome tools), open the page and check, against
   `docs/STYLE.md`:
   - **Light and dark mode** (toggle the site's theme button): text contrast,
     code blocks, tables, the `since` note.
   - **Phone width** (resize to about 390 px): no horizontal scrolling,
     tables readable, the app bar still usable.
   - Images: correct size, nothing above the fold lazy-loaded, alt text.
   - The page's place in the hub table and its Related links.
3. Fix anything off in the page (or report it if it's a template problem).
4. Close any tabs you opened.

## Outgoing edge

```bash
scripts/walk.sh transition --state "$STATE" --from visual_check --to terminal
```
