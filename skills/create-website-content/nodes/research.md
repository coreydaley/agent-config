# Node: research (Claude)

Find out what's true, on a real Mac, before writing anything. Every claim the
page will make about a tool, a command, a menu, a version or the app needs
evidence in the research log.

## Steps

1. **Sources.** Read the primary sources: the app repo (commits, code, tests;
   private, so nothing internal goes on the page), Apple's documentation,
   the competitor's own site or App Store page for a compare page, upstream
   project docs. Date every fact for compare pages ("Checked October 2026").
   Several independent sources can go to read-only research sub-agents that
   each write a source sheet into `$WORK_DIR`.

2. **Hands-on tests.** Run every tool and command the page will mention,
   against real or realistic files:
   - Built-in tools first (`tar`, `unzip`, `ditto`, Archive Utility via
     `open -g -a "Archive Utility" <copy>`), then Homebrew tools.
   - Generate test files where you can (`zip`, `7zz a`, `magick`, `hdiutil`).
   - Real samples (installers, archives from a vendor) need the user's OK to
     download: name the file, source and size. Put them in
     `$WORK_DIR/samples/`, never run them, and record their SHA-256.
   - Installing a tool (`brew install`) also needs the user's OK.
   - Work only in `$WORK_DIR` or the scratchpad, never in the user's folders.
     Anything that changes the user's system (a Shortcuts automation, a
     launchd job) needs their OK and is removed afterwards.
   - Note the macOS version (`sw_vers -productVersion`) and tool versions.

3. **Write `$WORK_DIR/research-log.md`**: each claim, the exact command or
   source, the output (trimmed), and a verdict: verified / false / untested.
   False and untested claims don't go on the page as fact.

4. **Things to report, not fix:** a bug or stale message in an app, a wrong
   statement on another page of the site. List them for the final summary.

## Outgoing edge

```bash
scripts/walk.sh transition --state "$STATE" --from research --to draft
```

On a `retest` loop back from `fact_check`, test only the claims the
fact-check flagged, then return to `draft`.
