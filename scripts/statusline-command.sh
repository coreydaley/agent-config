#!/usr/bin/env bash
# Claude Code statusline
# Reads JSON from stdin; emits a single-line status.

set -o pipefail

input=$(cat)

jqget() { echo "$input" | jq -r "$1" 2>/dev/null; }

model=$(jqget '.model.display_name // "Claude"')
session=$(jqget '.session_name // ""')
cwd=$(jqget '.workspace.current_dir // .cwd // "."')
cost=$(jqget '.cost.total_cost_usd // 0')
rate_5h=$(jqget '.rate_limits.five_hour.used_percentage // empty')
rate_7d=$(jqget '.rate_limits.seven_day.used_percentage // empty')
resets_5h=$(jqget '.rate_limits.five_hour.resets_at // empty')
resets_7d=$(jqget '.rate_limits.seven_day.resets_at // empty')

# ANSI helpers
c() { printf "\033[%sm%s\033[0m" "$1" "$2"; }
DIM="2;37"
SEP=" $(c "$DIM" "•") "
GROUP_SEP=" $(c "$DIM" "│") "

claude_seg=()
env_seg=()

# ── Claude info ──
claude_seg+=("$(c "1;35" "$model")")



# Percentage with color: green <33%, orange <66%, red >=66%
pct_color() {
  local pct=$1
  local col="32"
  (( pct >= 50 )) && col="38;5;208"
  (( pct >= 80 )) && col="31"
  c "$col" "${pct}%"
}

# Format seconds remaining as compact human-readable string
fmt_remaining() {
  local secs=$1
  if (( secs <= 0 )); then echo "now"; return; fi
  local d=$(( secs / 86400 ))
  local h=$(( (secs % 86400) / 3600 ))
  local m=$(( (secs % 3600) / 60 ))
  if (( d > 0 ));   then echo "${d}d${h}h"
  elif (( h > 0 )); then echo "${h}h${m}m"
  else                   echo "${m}m"
  fi
}

# Context %, color by fill level
pct=$(jqget '.context_window.used_percentage // empty')
pct=${pct%.*}
if [[ -n "$pct" && "$pct" -gt 0 ]]; then
  claude_seg+=("$(pct_color "$pct")")
fi

# Cost
if awk -v x="$cost" 'BEGIN{exit !(x+0>0)}'; then
  claude_seg+=("$(c "$DIM" "$(printf '$%.2f' "$cost")")")
fi

# Rate limits — only present after first API response in a session
now_ts=$(date +%s)
rate_segs=()
if [[ -n "$rate_5h" ]]; then
  pct5=${rate_5h%.*}
  label="$(pct_color "$pct5")"
  if [[ -n "$resets_5h" ]]; then
    label+="$(c "2;37" "/$(fmt_remaining $(( resets_5h - now_ts )))")"
  fi
  rate_segs+=("$label")
fi
if [[ -n "$rate_7d" ]]; then
  pct7=${rate_7d%.*}
  label="$(pct_color "$pct7")"
  if [[ -n "$resets_7d" ]]; then
    label+="$(c "2;37" "/$(fmt_remaining $(( resets_7d - now_ts )))")"
  fi
  rate_segs+=("$label")
fi
if (( ${#rate_segs[@]} > 0 )); then
  rate_joined=""
  for r in "${rate_segs[@]}"; do
    [[ -z "$rate_joined" ]] && rate_joined="$r" || rate_joined="${rate_joined} ${r}"
  done
  claude_seg+=("$rate_joined")
fi

# ── Environment ──
# Directory: starship-style — repo-relative or ~-collapsed path, truncated to last 5 components
repo_root=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null)
if [[ -n "$repo_root" ]]; then
  repo_parent=$(basename "$(dirname "$repo_root")")
  repo_name=$(basename "$repo_root")
  rel=${cwd#$repo_root}; rel=${rel#/}
  dir_path="$repo_parent/$repo_name${rel:+/$rel}"
else
  dir_path="${cwd/#$HOME/~}"
fi
# Keep only the last 5 path components
while (( $(awk -F/ '{print NF}' <<< "$dir_path") > 5 )); do
  dir_path="${dir_path#*/}"
done
dir_piece="$(c "1;34" "[$dir_path]")"
env_seg+=("$dir_piece")

git_piece=""
if git -C "$cwd" rev-parse --is-inside-work-tree &>/dev/null; then
  branch=$(git -C "$cwd" branch --show-current 2>/dev/null)
  [[ -z "$branch" ]] && branch=$(git -C "$cwd" rev-parse --short HEAD 2>/dev/null)

  # File status counts (starship-style)
  staged_n=0; modified_n=0; deleted_n=0; untracked_n=0; renamed_n=0; conflicted_n=0
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    x="${line:0:1}"; y="${line:1:1}"
    if [[ "$x$y" == "??" ]]; then
      ((untracked_n++))
    elif [[ "$x" == "U" || "$y" == "U" || "$x$y" == "AA" || "$x$y" == "DD" ]]; then
      ((conflicted_n++))
    else
      [[ "$x" == "R" ]] && ((renamed_n++))
      [[ "$x" != " " && "$x" != "?" && "$x" != "R" ]] && ((staged_n++))
      [[ "$y" == "M" ]] && ((modified_n++))
      [[ "$y" == "D" ]] && ((deleted_n++))
    fi
  done < <(git -C "$cwd" status --porcelain=v1 2>/dev/null)

  # Ahead/behind vs upstream
  ahead_n=0; behind_n=0
  if git -C "$cwd" rev-parse --abbrev-ref '@{upstream}' &>/dev/null; then
    read -r behind_n ahead_n <<< "$(git -C "$cwd" rev-list --left-right --count '@{upstream}...HEAD' 2>/dev/null)"
    behind_n=${behind_n:-0}; ahead_n=${ahead_n:-0}
  fi

  # Stash count
  stashed_n=$(git -C "$cwd" rev-list --walk-reflogs --count refs/stash 2>/dev/null || echo 0)

  git_piece="$(c "1;90" "⎇ $branch")"
  (( conflicted_n > 0 )) && git_piece+=" $(c "1;31" "=$conflicted_n")"
  (( staged_n > 0 ))     && git_piece+=" $(c "1;32" "+$staged_n")"
  (( modified_n > 0 ))   && git_piece+=" $(c "1;33" "!$modified_n")"
  (( deleted_n > 0 ))    && git_piece+=" $(c "1;31" "✘$deleted_n")"
  (( renamed_n > 0 ))    && git_piece+=" $(c "1;36" "»$renamed_n")"
  (( untracked_n > 0 ))  && git_piece+=" $(c "1;36" "?$untracked_n")"
  (( stashed_n > 0 ))    && git_piece+=" $(c "1;34" "\$$stashed_n")"
  if (( ahead_n > 0 && behind_n > 0 )); then
    git_piece+=" $(c "1;33" "⇡$ahead_n⇣$behind_n")"
  else
    (( ahead_n > 0 ))  && git_piece+=" $(c "1;32" "⇡$ahead_n")"
    (( behind_n > 0 )) && git_piece+=" $(c "1;31" "⇣$behind_n")"
  fi
  env_seg+=("$git_piece")
fi

left=""
for i in "${!claude_seg[@]}"; do
  if (( i == 0 )); then left="${claude_seg[$i]}"
  else left="${left}${SEP}${claude_seg[$i]}"
  fi
done

right=""
for i in "${!env_seg[@]}"; do
  if (( i == 0 )); then right="${env_seg[$i]}"
  else right="${right}${SEP}${env_seg[$i]}"
  fi
done

# Middle line: claude info + dir (git moved to its own line below)
middle=""
if [[ -n "$left" && -n "$dir_piece" ]]; then
  middle="${left}${GROUP_SEP}${dir_piece}"
elif [[ -n "$left" ]]; then
  middle="$left"
else
  middle="$dir_piece"
fi

printf "%b" "$middle"
[[ -n "$git_piece" ]] && printf "\n%b" "$git_piece"
exit 0
