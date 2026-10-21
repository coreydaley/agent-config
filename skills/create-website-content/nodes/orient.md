# Node: orient

Decide exactly what page this is, learn the rules for that page type, and see
how the site already handles neighboring topics.

## Steps

1. **Read the rules.** In `$REPO_ROOT` (`~/Code/github.com/coreydaley/coreydaley-dev/main`):
   - `CLAUDE.md`, especially **Accuracy (posts and app pages)**, **App pages**,
     and **Apps and projects** (params, landing section kinds, shortcodes:
     `since`, `price`, `shot`, `appstore`, `anchor`, `if-published`).
   - `docs/STYLE.md` for look and feel.

2. **Pin the page type and its location:**

   | Type | Where | Front matter |
   |---|---|---|
   | answer | `content/apps/<app>/<slug>.md` | YAML: `title`, `description` ≤170, `date`, `sitemap`, `topics` |
   | help | `content/apps/<app>/help/<slug>.md` | YAML: `title`, `description`, `weight`, `topics`, `since` if unreleased |
   | compare | `content/apps/<app>/compare/<competitor>.md` | YAML: `title`, `description`, `checked:` date, `sitemap`, `topics` |
   | landing | `content/apps/<app>/_index.md` → `landing.sections` | an existing section `kind` |
   | site | `content/<slug>.md` | per the page's neighbors |

3. **Read two or three neighbors of the same type** in that app (and the
   one closest in topic) for voice, structure and `topics` values. Only use
   `topics` values that already exist in that app.

4. **Check overlap.** Search `content/` for pages already answering this
   question (`grep -ril`). Prefer updating an existing page to creating a
   near-duplicate. Note the hub page (`/apps/purrchiver/archive-wont-open-mac/`
   for "won't open" questions) and related help pages that should link here.

5. **Search demand (answer pages).** If the topic came from Search Console or
   Bing queries, record the queries and their impressions. Shape the title and
   first paragraph around the question people actually type.

6. **Which release?** For anything an app does, check the app repo (`main` is
   the next release; compare its `MARKETING_VERSION` with the site's
   `appStoreVersion`). Unreleased behavior gets `{{< since "x.y" >}}`.

7. **Slug and work dir:**
   ```bash
   WORK_DIR="$HOME/Reports/coreydaley/coreydaley-dev/site-pages/$SLUG"
   mkdir -p "$WORK_DIR/samples"
   scripts/walk.sh set --state "$STATE" --key slug     --value "$SLUG"
   scripts/walk.sh set --state "$STATE" --key page_type --value "$TYPE"
   scripts/walk.sh set --state "$STATE" --key target   --value "<content path>"
   scripts/walk.sh set --state "$STATE" --key work_dir --value "$WORK_DIR"
   ```

## Deliverable

A short **Orientation Summary**: the question the page answers, type, target
path, neighbors read, overlap found, hub and links to add, release status,
and the list of claims that will need hands-on testing.

## Outgoing edge

```bash
scripts/walk.sh transition --state "$STATE" --from orient --to research
```
