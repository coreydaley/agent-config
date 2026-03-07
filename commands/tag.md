---
description: Analyze commits since the last git tag and create the next semantic version tag using conventional commit rules.
disable-model-invocation: true
---

# Tag

Analyze commits since the last git tag and create the next semantic version tag.

## Instructions

1. **Fetch all tags and find the latest one** by running:
   - `git tag --sort=-version:refname | head -20` to list tags sorted by version descending
   - If no tags exist, the starting version is `0.0.0` and all commits in the repo are in scope
   - The latest tag is the first result; parse it as a semver string `vMAJOR.MINOR.PATCH` (strip a leading `v` if present)

2. **Collect commits since the last tag** by running:
   - `git log <last-tag>..HEAD --oneline --no-merges` (or `git log --oneline --no-merges` if no prior tag exists)
   - If there are no commits since the last tag, stop and inform the user that there is nothing to tag

3. **Determine the version bump** by scanning the commit messages using these rules in order of precedence (highest wins):

   | Indicator | Bump |
   |-----------|------|
   | Any commit message contains `BREAKING CHANGE` in the body/footer | **major** |
   | Any commit type ends with `!` (e.g. `feat!:`, `fix!:`) | **major** |
   | Any commit starts with `feat:` or `feat(...):`  | **minor** |
   | Any other conventional commit (`fix:`, `perf:`, `refactor:`, `docs:`, `chore:`, `test:`, `style:`, `ci:`, `build:`) | **patch** |
   | No recognizable conventional commit prefix | **patch** (default) |

   Apply the winning bump to the current version:
   - **major**: increment MAJOR, reset MINOR and PATCH to 0
   - **minor**: increment MINOR, reset PATCH to 0
   - **patch**: increment PATCH only

4. **Show the user a summary** before creating the tag:
   - Current version (or "none" if no prior tag)
   - Proposed new version
   - Bump type and the commit(s) that drove it
   - Full list of commits being tagged

5. **Ask the user to confirm** before creating the tag using `AskUserQuestion`:
   - Present the proposed version and bump type
   - Options: "Yes, create the tag" / "No, cancel" / "Override version manually"
   - If the user cancels or provides a different version, act accordingly and stop or re-run with the override

6. **Create the annotated tag** with a multi-line message summarizing the changes:
   - Compose a concise bullet-point summary of the commits (group related changes, skip noise like formatting/typo fixes unless they're the only changes)
   - Use the format:
     ```
     git tag -a v<new-version> -m "v<new-version>

     - <bullet 1>
     - <bullet 2>
     ..."
     ```
   - Keep bullets short (one line each), written in present tense, focused on what changed from a user/developer perspective
   - Use `v` prefix on the tag name (e.g. `v1.2.3`)

7. **Confirm success** by running `git tag --sort=-version:refname | head -5` and displaying the output so the user can see the new tag at the top of the list.

8. **Remind the user** to push the tag when ready:
   ```
   git push origin v<new-version>
   ```
   Do NOT push automatically — let the user decide when to push.

## Constraints

- Never delete or move existing tags
- Never force-create a tag (`-f`) unless the user explicitly requests it
- If $ARGUMENTS is provided and looks like a version string (e.g. `1.4.0` or `v1.4.0`), skip the bump calculation and use that version directly (still show the commit summary)
- If $ARGUMENTS is provided and is a bump type (`major`, `minor`, or `patch`), override the auto-detected bump with that value
