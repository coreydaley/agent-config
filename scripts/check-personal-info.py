#!/usr/bin/env python3
"""Block personal or embarrassing information from this public repository.

Complements gitleaks (which catches secrets). Two layers:

Generic checks (in-repo, safe to publish):
  - home-network hostnames (*.local, *.lan, *.home.arpa)
  - private IPv4 addresses (10/8, 172.16/12, 192.168/16)
  - email addresses
  - phone numbers
  - absolute home-directory paths (/Users/<name>/, /home/<name>/) -- use ~

Private denylist (never committed): every regex in
  $AGENT_CONFIG_DENYLIST, default ${XDG_CONFIG_HOME:-~/.config}/agent-config/denylist
one per line, '#' comments allowed, matched case-insensitively. Put names,
employers, addresses, amounts, codenames, etc. there -- the list itself is
personal, so it lives outside the repo. Matches are reported without echoing
the line.

Allowlist: .personal-info-allow (regexes, one per line) for known-safe
matches. A line containing "personal-info: allow" is skipped.

Usage:
  scripts/check-personal-info.py --staged   # added lines in the index (pre-commit)
  scripts/check-personal-info.py --all      # every tracked file (pre-push / CI)
"""
import os
import re
import subprocess
import sys
from pathlib import Path

GENERIC = [
    ("hostname", r"\b[A-Za-z0-9-]+\.(?:local|lan|home\.arpa)\b"),
    ("private IP", r"\b(?:10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}\b"),
    ("email", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    ("phone number", r"(?<![\w.-])(?:\+?1[ .-]?)?\(?[2-9]\d{2}\)?[ .-]\d{3}[ .-]\d{4}(?![\w.-])"),
    ("home path", r"/(?:Users|home)/[A-Za-z0-9._-]+/"),
]
SKIP_MARKER = "personal-info: allow"
ALLOW_FILE = ".personal-info-allow"


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def load_regexes(path, flags=0):
    p = Path(path).expanduser()
    if not p.is_file():
        return None
    out = []
    for raw in p.read_text().splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            out.append(re.compile(line, flags))
    return out


def staged_lines():
    diff = git("diff", "--cached", "-U0", "--no-color", "--diff-filter=ACM", "--", ".", f":!{ALLOW_FILE}")
    path, num = None, 0
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
        elif line.startswith("@@"):
            num = int(re.search(r"\+(\d+)", line).group(1))
        elif line.startswith("+") and path:
            yield path, num, line[1:]
            num += 1


def all_lines():
    for path in git("ls-files", "-z").split("\0"):
        if not path or path == ALLOW_FILE:
            continue
        try:
            data = Path(path).read_bytes()
        except (FileNotFoundError, IsADirectoryError):
            continue
        if b"\0" in data[:8192]:
            continue
        for num, line in enumerate(data.decode("utf-8", "replace").splitlines(), 1):
            yield path, num, line


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--staged"
    if mode not in ("--staged", "--all"):
        sys.exit(__doc__)
    os.chdir(git("rev-parse", "--show-toplevel").strip())

    allow = load_regexes(ALLOW_FILE) or []
    deny_path = os.environ.get("AGENT_CONFIG_DENYLIST") or os.path.join(
        os.environ.get("XDG_CONFIG_HOME", "~/.config"), "agent-config", "denylist")
    deny = load_regexes(deny_path, re.IGNORECASE)
    generic = [(label, re.compile(rx)) for label, rx in GENERIC]

    found = 0
    lines = staged_lines() if mode == "--staged" else all_lines()
    for path, num, text in lines:
        if SKIP_MARKER in text:
            continue
        for label, rx in generic:
            for m in rx.finditer(text):
                if not any(a.search(m.group(0)) for a in allow):
                    print(f"BLOCKED ({label}): {path}:{num}: {m.group(0)}", file=sys.stderr)
                    found += 1
        for rx in deny or []:
            if rx.search(text):
                print(f"BLOCKED (denylist): {path}:{num} matches a private denylist pattern", file=sys.stderr)
                found += 1
                break

    if found:
        print(f"\n{found} personal-info match(es). Remove them, or if a match is genuinely safe,\n"
              f"add a regex to {ALLOW_FILE} or append '{SKIP_MARKER}' to the line.", file=sys.stderr)
        return 1
    if deny is None:
        print(f"note: no private denylist at {deny_path} (generic checks only)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
