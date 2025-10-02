#!/usr/bin/env bash
set -euo pipefail

ON_org="${1:-OpenNeuroDatasets}"
OUTFILE="${2:-$(dirname "$0")/openneuro_repos.tsv}"
LIMIT="${3:-9999}"

mkdir -p "$(dirname "$OUTFILE")"
touch "$OUTFILE"

echo "Fetching up to $LIMIT repos for org '$ON_org'..."
repos_json=$(gh repo list "$ON_org" --limit "$LIMIT" --json name,url)

# Build lines: name<TAB>url
mapfile -t lines < <(echo "$repos_json" | jq -r '.[] | "\(.name)\t\(.url)"')

# Write lines
added=0
for line in "${lines[@]}"; do
  if ! grep -xFq "$line" "$OUTFILE"; then
    printf '%s\n' "$line" >> "$OUTFILE"
    added=$((added + 1))
  fi
done

echo "Appended $added new repos. Total lines in $OUTFILE: $(wc -l < \"$OUTFILE\")"