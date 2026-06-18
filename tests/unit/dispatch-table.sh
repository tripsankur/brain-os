#!/usr/bin/env bash
# Verify every subcommand in brain.md dispatch table points to an existing file
# Reads from core/brain.md; checks core/subcommands/{name}.md exists

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BRAIN_MD="$REPO_ROOT/core/brain.md"
FAIL=0

if [[ ! -f "$BRAIN_MD" ]]; then
  echo "  SKIP: core/brain.md not found (P1 migration not yet complete)"
  exit 0
fi

# Extract subcommand names from dispatch table lines: | `name` | path |
while IFS= read -r line; do
  if [[ "$line" =~ ^\|[[:space:]]*\`([a-z-]+)\` ]]; then
    name="${BASH_REMATCH[1]}"
    expected="$REPO_ROOT/core/subcommands/${name}.md"
    if [[ ! -f "$expected" ]]; then
      echo "  MISSING: core/subcommands/${name}.md (referenced in dispatch table)"
      ((FAIL++))
    fi
  fi
done < "$BRAIN_MD"

[[ "$FAIL" -eq 0 ]]
