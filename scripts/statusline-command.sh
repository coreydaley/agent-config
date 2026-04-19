#!/usr/bin/env bash
# Claude Code status line — Starship-inspired
# Segments: model | cwd | git branch | session name | context remaining | rate limits

input=$(cat)

# --- parse fields ---
model=$(echo "$input" | jq -r '.model.display_name // empty')
session=$(echo "$input" | jq -r '.session_name // empty')
cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // empty')
ctx_remaining=$(echo "$input" | jq -r '.context_window.remaining_percentage // empty')
rate_5h=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
rate_7d=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')

# --- ANSI colors (dim-friendly: no bold, standard palette) ---
reset='\033[0m'
blue='\033[34m'
purple='\033[35m'
gray='\033[37m'
green='\033[32m'
amber='\033[33m'
red='\033[31m'
dim='\033[2m'

parts=()

# model name
if [ -n "$model" ]; then
  parts+=("$(printf "${blue}%s${reset}" "$model")")
fi

# cwd — abbreviated Starship-style: ~ for home, truncate to last 3 segments
if [ -n "$cwd" ]; then
  home_dir="$HOME"
  display_cwd="${cwd/#$home_dir/\~}"
  IFS='/' read -ra segs <<< "$display_cwd"
  if [ "${#segs[@]}" -gt 3 ]; then
    display_cwd="…/${segs[-2]}/${segs[-1]}"
  fi
  parts+=("$(printf "${green}%s${reset}" "$display_cwd")")
fi

# git branch — skip optional locks to avoid hangs
if [ -n "$cwd" ] && cd "$cwd" 2>/dev/null; then
  branch=$(git -c core.fsmonitor=false --no-optional-locks symbolic-ref --short HEAD 2>/dev/null \
           || git -c core.fsmonitor=false --no-optional-locks rev-parse --short HEAD 2>/dev/null)
  if [ -n "$branch" ]; then
    parts+=("$(printf "${gray}⎇  %s${reset}" "$branch")")
  fi
fi

# session name
if [ -n "$session" ]; then
  parts+=("$(printf "${purple}[%s]${reset}" "$session")")
fi

# context remaining %
if [ -n "$ctx_remaining" ]; then
  pct=$(printf '%.0f' "$ctx_remaining")
  if   [ "$pct" -ge 50 ]; then color="$green"
  elif [ "$pct" -ge 20 ]; then color="$amber"
  else                          color="$red"
  fi
  parts+=("$(printf "${dim}ctx:${reset}${color}%s%%${reset}" "$pct")")
fi

# rate limits
rate_parts=()
if [ -n "$rate_5h" ]; then
  pct=$(printf '%.0f' "$rate_5h")
  rate_parts+=("$(printf "5h:%s%%" "$pct")")
fi
if [ -n "$rate_7d" ]; then
  pct=$(printf '%.0f' "$rate_7d")
  rate_parts+=("$(printf "7d:%s%%" "$pct")")
fi
if [ "${#rate_parts[@]}" -gt 0 ]; then
  joined=$(IFS=' '; echo "${rate_parts[*]}")
  parts+=("$(printf "${amber}%s${reset}" "$joined")")
fi

# --- join with separator ---
sep="$(printf "${dim}  ${reset}")"
result=""
for part in "${parts[@]}"; do
  if [ -z "$result" ]; then
    result="$part"
  else
    result="${result}${sep}${part}"
  fi
done

printf "%b\n" "$result"
