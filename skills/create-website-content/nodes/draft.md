# Node: draft (Claude)

Write the page to `$WORK_DIR/$SLUG-draft.md` (for a landing section, write the
YAML block that will go into `_index.md`).

## Rules

- Follow `CLAUDE.md` (Accuracy, App pages) and `docs/STYLE.md` exactly.
- **Answer first.** The first paragraph says what the thing is and what works.
  Free and built-in options come before the app. Then what the app does and
  doesn't do, under `{{< since >}}` if it isn't released.
- **Only verified claims**, worded as narrowly as the evidence: "I tested this
  on macOS 27 with …", "I haven't measured …". Name versions.
- **Commands are copy-pasteable** and safe from any working directory: create
  output folders (`mkdir -p`), pass explicit output paths, quote paths.
- **Front matter** per the type table in `orient`; `description` ≤170
  characters and specific; no `image` unless the type uses one.
- **Screenshots** use `{{< shot >}}` with a capture brief; a shot with no
  `src` renders nothing, so it's safe to leave as a placeholder.
- **Compare pages:** every fact sourced and dated, a "Choose <competitor>
  if…" section that recommends them where they're the better fit, no trash
  talk, sources listed at the bottom.
- **Related** links at the end: the hub, `help/other-tools/` where relevant,
  and the closest neighbor pages.

## Outgoing edge

```bash
scripts/walk.sh transition --state "$STATE" --from draft --to fact_check
```
