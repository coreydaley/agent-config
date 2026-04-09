---
description: Create a new standalone script in ~/Code/sandbox/scripts/
---

# Create Sandbox Script

Create a new standalone script in the sandbox.

## Step 1: Gather details

Parse `$ARGUMENTS` for any details already provided (name, language, purpose). Then check what is still missing.

If **name** is missing, or if `$ARGUMENTS` is empty, ask for all needed details in a single message using this exact format:

> Please provide the following details for the new script:
>
> - **Name** (required) — filename without extension, e.g. `fetch-github-stars`
> - **Language** — `python`, `bash`, `node`, etc. (default: `python`)
> - **Purpose** — one-liner describing what the script does (optional)

Wait for the user's response before proceeding.

## Step 2: Create the script

Determine the file extension from the language (`python` → `.py`, `bash` → `.sh`, `node` → `.js`, etc.).

Create the file at `~/Code/sandbox/scripts/<name>.<ext>` with a minimal starter appropriate for the language:

- **Python**: shebang `#!/usr/bin/env python3` and a `main()` function stub
- **Bash**: shebang `#!/usr/bin/env bash` and `set -euo pipefail`
- **Node**: `#!/usr/bin/env node` and a minimal async main stub

For bash scripts, make the file executable:
```bash
chmod +x ~/Code/sandbox/scripts/<name>.sh
```

If a purpose was provided, add it as a brief comment at the top of the file.

## Step 3: Confirm

Report the full path of the created script.
