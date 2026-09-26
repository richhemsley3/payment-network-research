#!/usr/bin/env bash
# Runs the station script over every property, four at a time. Logs to the scratchpad.
# usage: bash tools/walk-all.sh [list-file]   (default tools/properties.txt: slug|url|tier|label)
cd "$(dirname "$0")/.."
LIST="${1:-tools/properties.txt}"
LOG="/private/tmp/claude-501/-Users-richhemsley-Desktop-Claude/a7b17a35-5948-40cb-a79f-825d4720b44b/scratchpad/walks"
mkdir -p "$LOG"
export NODE_PATH="$(pwd)/../node_modules"
grep -v '^#' "$LIST" | grep '|' | while IFS='|' read -r slug url tier label; do
  echo "$slug|$url|$tier|$label"
done | xargs -P 4 -I{} bash -c 'IFS="|" read -r slug url tier label <<< "{}"; out="'"$LOG"'/${slug}${label:+-$label}.log"; echo "start $slug $label $(date +%H:%M:%S)"; node tools/walk.js "$slug" "$url" "$tier" $label > "$out" 2>&1; echo "done  $slug $label $(date +%H:%M:%S) $(tail -2 "$out" | head -1)"'
