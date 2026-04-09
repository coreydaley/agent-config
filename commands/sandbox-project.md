---
description: Create a new project directory in ~/Code/sandbox/projects/
---

# Create Sandbox Project

Create a new project in the sandbox for experiments, POCs, and prototypes.

## Step 1: Gather details

Parse `$ARGUMENTS` for any details already provided (name, purpose, language/stack). Then check what is still missing.

If **name** is missing, or if `$ARGUMENTS` is empty, ask for all needed details in a single message using this exact format:

> Please provide the following details for the new project:
>
> - **Name** (required) — directory name, e.g. `vector-search-poc`, `auth-spike`
> - **Purpose** — one-liner describing the experiment or goal (optional)
> - **Stack** — language or framework, e.g. `python`, `node`, `go`, `react` (optional)

Wait for the user's response before proceeding.

## Step 2: Create the project

Create the project directory at `~/Code/sandbox/projects/<name>/`.

Bootstrap minimally based on the stack if provided:

- **Python**: create `main.py` with a `main()` stub and `requirements.txt` (empty)
- **Node**: create `index.js` with a minimal stub and `package.json` (`npm init -y`)
- **Go**: create `main.go` with `package main` and `func main()`
- **React**: note that you can scaffold with `npm create vite@latest` and suggest the user run it, since it requires interactive input
- **No stack / unknown**: create an empty `README` (no extension) with the project name and purpose as the only content

If a purpose was provided, add it as a comment at the top of the entry-point file (or as the README content).

## Step 3: Confirm

Report the full path of the created project directory and any files created.
