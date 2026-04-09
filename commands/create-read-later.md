---
description: Add a URL to the Read Later list in the Obsidian vault
---

# Add to Read Later

Add a new entry to `Read Later.md` in the Obsidian vault.

## Step 1: Get the URL

If a URL is present in `$ARGUMENTS`, use it. Otherwise ask:

> What URL would you like to add to your Read Later list?

## Step 2: Fetch the page title

Use the WebFetch tool to retrieve the page title from the URL. Extract the article/page title, stripped of site name suffixes (e.g. " | Anthropic", " - Coursera", " | LinkedIn"). If fetching fails, ask the user for a title.

## Step 3: Prepend the entry

Read `Read Later.md`, then insert a new list item immediately after the `# Read Later` heading line:

```
- [ ] [<title>](<url>)
```

Use the Edit tool to insert the line after the heading.

## Step 4: Confirm

Report the title and URL that were added.
