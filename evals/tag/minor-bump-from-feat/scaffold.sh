#!/usr/bin/env bash
set -euo pipefail
export GIT_AUTHOR_NAME=Eval GIT_AUTHOR_EMAIL=eval@example.com
export GIT_COMMITTER_NAME=Eval GIT_COMMITTER_EMAIL=eval@example.com
git init -q -b main
c() { echo "$1" >> log.txt; git add log.txt; git commit -q -m "$1"; }
c "chore: initial commit"
git tag -a v1.2.0 -m v1.2.0
c "fix: handle empty config"
c "feat(cli): add --dry-run flag"
c "docs: update readme"
