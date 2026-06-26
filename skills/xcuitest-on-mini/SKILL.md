---
disable-model-invocation: false
name: xcuitest-on-mini
description: >-
  Run XCUITest (or any xcodebuild test invocation) on the user's Mac
  mini instead of the local Mac, so the "Automation Running" indicator
  doesn't steal the local screen during agentic dev. Rsyncs the local
  working tree (no git involvement — just files), runs xcodebuild on
  the mini, streams results back via SSH. Optional `--pull-xcresult`
  brings the failure result bundle back for local Xcode inspection.
  Use when: the user asks to "run UI tests on the mini", "remote test",
  "test without locking my screen", or after a code change that needs
  UI verification before committing.
argument-hint: "[<test-filter>] [--all] [--scheme NAME] [--project PATH] [--pull-xcresult]"
---
disable-model-invocation: false

# xcuitest-on-mini — remote XCUITest on the Mac mini

## When to use

The Apple-ecosystem XCUITest grabs the screen via the "Automation
Running" indicator for the duration of a UI test run. On a developer's
primary Mac that interrupts everything else they're doing. The user
has a Mac mini (`mac-mini.example`) sitting there as the CI
runner — use it for ad-hoc UI test runs too.

This skill exists because:

- The "skip UI tests during agentic dev" convention defers regressions
  to the end of the wave, producing multi-hour debugging sessions when
  the suite finally runs. Running them on the mini gives a fast remote
  signal without the screen cost.
- Push-to-CI works but adds git + GHA-queue latency. SSH + rsync is
  faster for the inner loop.
- Xcode Server (Apple's old "use a remote Mac" feature) was killed
  with macOS Server. Xcode Cloud is the official replacement but
  doesn't let you point at your own hardware. This is the manual
  equivalent.

## How it works

1. Detects the project's `.xcodeproj` from cwd (BFS up to depth 3) and
   prefers a sibling `.xcworkspace` when one exists — local SPM package
   test targets only resolve through the workspace, so `--all` against
   the workspace is the real everything (SPM + app unit + UI); against
   a bare project the package suites would silently not run.
2. Pre-creates the destination dir on the mini.
3. Rsyncs the local working tree → a **dedicated staging dir** on the
   mini (`$XCUITEST_ON_MINI_DIR`, default `~/.xcuitest-on-mini`)
   with the local path preserved beneath it. Excludes `.git`, `build/`,
   `DerivedData/`, `.build/`, `node_modules/`, `xcuserdata/`,
   `*.xcresult`, etc. — only source files travel.
4. SSHes to the mini, runs `xcodebuild test` with the supplied filter
   (defaults to `<scheme>UITests`), pipes through `xcbeautify` if
   available.
5. On failure with `--pull-xcresult`, rsyncs the `.xcresult` bundle
   back to `<repo>/build/remote-ui-tests.xcresult/` for local Xcode
   inspection.

Path mapping is **namespaced, not identity**: `$LOCAL_ROOT` becomes
`$XCUITEST_ON_MINI_DIR$LOCAL_ROOT` on the mini (e.g.
`~/.xcuitest-on-mini~/Code/.../main`). The mini
is the CI / test runner host and has its own
checkouts at the live `~/Code/...` paths — mirroring under a
dedicated staging dir keeps the `rsync --delete` from ever clobbering
them. Side benefits: each worktree gets a collision-free mirror, and
Xcode keys DerivedData by source-path hash so the mirror builds in its
own bucket instead of fighting the mini's checkout. Nothing depends on
the path being identical, only stable + writable. Override the base via
`XCUITEST_ON_MINI_DIR`.

## Help mode

If `--help` / `-h` in args, run the script with `--help` to print
the long-form usage and stop:

```bash
bash scripts/run.sh --help
```

## What to do

1. Parse args.
2. Run the script, forwarding all args verbatim:

   ```bash
   bash scripts/run.sh "$@"
   ```

3. Echo the script's output. Exit with its exit code.

## Don'ts

- **Don't** require a git clone on the mini. Rsync is the whole
  transport; no remote git state needed.
- **Don't** push to a git remote just to test. The point of this
  skill is to test uncommitted state without polluting branch history.
- **Don't** start a concurrent xcodebuild if one is already running
  on the mini. XCUITest grabs the screen exclusively; the script
  refuses with a friendly error if a `pgrep xcodebuild` finds one.
- **Don't** copy `.git` to the mini. The build doesn't need it; it
  just bloats the rsync.
- **Don't** invent test filters. If the user doesn't supply one, the
  script defaults to `<scheme>UITests` (the conventional UI test
  target name). If their project doesn't follow that convention, the
  user has to pass the filter explicitly.

## Setup expectations

- The Mac mini must be reachable as `corey@mac-mini.example`
  via SSH key auth (no password).
- Xcode must be installed on the mini at the canonical location.
- `brew install xcbeautify` on the mini is optional but nicer
  output.
- For `--pull-xcresult` to be useful, the local user needs Xcode to
  open the bundle.
- **Auto-login must be enabled** on the mini, and the login keychain
  must be unlocked (auto-unlocks on GUI login). XCUITest needs a
  real WindowServer + accessible keychain; no GUI session means no
  signing identity available.
- **Passwordless sudo for the runner user** — required because the
  script wraps xcodebuild in `sudo launchctl asuser <UID> sudo -u
  <USER>` to inject the SSH command into the GUI user's launchd
  domain (where codesign can access the signing identity). On a
  dedicated single-user CI Mac mini, configure
  `/etc/sudoers.d/<user>` with:
  ```
  <user> ALL=(ALL) NOPASSWD: ALL
  ```
  Targeted alternatives (`/bin/launchctl, /usr/bin/sudo, /bin/rm`)
  also work but the ALL form is simpler. The Mac mini is presumed
  single-purpose; if it weren't, the security calculus would shift.

Override hostname / user / staging dir via env if you ever stand up a
second runner:

- `XCUITEST_ON_MINI_HOST=…`
- `XCUITEST_ON_MINI_USER=…`
- `XCUITEST_ON_MINI_DIR=…` (remote staging base; default
  `~/.xcuitest-on-mini`)

## Why the double sudo + launchctl dance

SSH sessions on macOS land in a different launchd domain than the
console (GUI) session. The login keychain is unlocked for the GUI
session (assuming auto-login + a one-time `security
set-key-partition-list -S apple-tool:,apple: -s …`), but SSH
sessions can't see that unlock state — codesign returns
`errSecInternalComponent` when it tries to access the signing
identity.

`launchctl asuser <UID> <command>` runs the command in the target
user's launchd domain. Switching audit sessions requires root, so
sudo is needed. Inside the asuser context we're still root, so a
second `sudo -u <user>` drops back to the original user so xcodebuild
writes its artifacts to `/Users/<user>/Library/Developer/...` and
not `/var/root/Library/Developer/...`.

Result: the SSH command behaves identically to running xcodebuild
manually in the user's GUI Terminal session. Keychain access works,
artifacts land in the right place, no password prompts.

## ARGUMENTS

$ARGUMENTS
