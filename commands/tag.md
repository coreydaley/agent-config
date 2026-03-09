---
description: >-
  Analyze commits since the last git tag and create the next
  semantic version tag using conventional commit rules.
disable-model-invocation: true
---

# Tag

Analyze commits since the last git tag and create the next
semantic version tag.

## Instructions

1. **Check the current branch** by running
   `git branch --show-current`:
   - If the branch name does not look like a mainline branch
     (`main`, `master`, `release`, or a `release/*`
     pattern), warn the user and ask them to confirm before
     continuing — tagging a feature branch is usually a
     mistake

2. **Fetch all tags and find the latest one** by running:
   - `git tag --sort=-version:refname | head -20` to list
     tags sorted by version descending
   - If no tags exist, the starting version is `0.0.0` and
     all commits in the repo are in scope
   - The latest tag is the first result; strip a leading `v`
     if present and parse as `MAJOR.MINOR.PATCH`
   - If the latest tag cannot be parsed as semver (e.g.
     `release-1.0`, `deploy-20240101`), warn the user,
     display the tag, and ask them to confirm the base
     version to use before continuing

3. **Collect commits since the last tag** by running:
   - `git log <last-tag>..HEAD --oneline --no-merges` (or
     `git log --oneline --no-merges` if no prior tag exists)
   - If there are no commits since the last tag, stop and
     inform the user that there is nothing to tag

4. **Determine the version bump** by scanning the commit
   messages using these rules in order of precedence
   (highest wins):

   | Indicator | Bump |
   | --- | --- |
   | Commit message contains `BREAKING CHANGE` in body/footer | **major** |
   | Commit type ends with `!` (e.g. `feat!:`, `fix!:`) | **major** |
   | Commit starts with `feat:` or `feat(...):` | **minor** |
   | Other conventional commit (`fix:`, `perf:`, etc.) | **patch** |
   | No recognizable conventional commit prefix | **patch** (default) |

   Apply the winning bump to the current version:
   - **major**: increment MAJOR, reset MINOR and PATCH to 0
   - **minor**: increment MINOR, reset PATCH to 0
   - **patch**: increment PATCH only

5. **Show the user a summary** before creating the tag:
   - Current version (or "none" if no prior tag)
   - Proposed new version
   - Bump type and the commit(s) that drove it
   - Full list of commits being tagged

6. **Ask the user to confirm** before creating the tag
   using `AskUserQuestion`:
   - Present the proposed version and bump type
   - Options: "Yes, create the tag" / "No, cancel" /
     "Override version manually"
   - If the user cancels or provides a different version,
     act accordingly and stop or re-run with the override

7. **Create the annotated tag** with a multi-line message
   summarizing the changes:
   - Compose a concise bullet-point summary of the commits
     (group related changes, skip noise like
     formatting/typo fixes unless they're the only changes)
   - Keep bullets short (one line each), written in present
     tense, focused on what changed from a user/developer
     perspective
   - Use a heredoc to avoid quoting issues with special
     characters in bullet text:

     <!-- markdownlint-disable MD033 -->

     ```bash
     git tag -a v<new-version> -m "$(cat <<'EOF'
     v<new-version>

     - <bullet 1>
     - <bullet 2>
     EOF
     )"
     ```

     <!-- markdownlint-enable MD033 -->

   - Always use the `v` prefix on the tag name (e.g.
     `v1.2.3`)

8. **Confirm success** by running
   `git tag --sort=-version:refname | head -5` and
   displaying the output so the user can see the new tag at
   the top of the list.

9. **Remind the user** to push the tag when ready:

   ```bash
   git push origin v<new-version>
   ```

   Do NOT push automatically — let the user decide when to
   push.

## Constraints

- Never delete or move existing tags
- Never force-create a tag (`-f`) unless the user
  explicitly requests it
- If `$ARGUMENTS` looks like a version string (e.g.
  `1.4.0` or `v1.4.0`): strip any leading `v`, use that
  version directly, and always add a `v` prefix when
  creating the tag name (still show the commit summary;
  skip steps 4 and 6)
- If `$ARGUMENTS` is a bump type (`major`, `minor`, or
  `patch`), override the auto-detected bump with that value
