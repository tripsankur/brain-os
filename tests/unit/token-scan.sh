#!/usr/bin/env bash
# Verify no hardcoded personal paths or unresolved tokens exist in core/ or modules/
# This is the P0/P1 gate check.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FAIL=0

check_pattern() {
  local label="$1"
  local pattern="$2"
  local dirs=("$REPO_ROOT/core" "$REPO_ROOT/modules")

  for dir in "${dirs[@]}"; do
    [[ -d "$dir" ]] || continue
    # Exclude _deprecated/ — archived files may retain original content
    matches=$(grep -rl "$pattern" "$dir" --exclude-dir="_deprecated" 2>/dev/null || true)
    if [[ -n "$matches" ]]; then
      echo "  FAIL [$label] found in:"
      echo "$matches" | sed 's/^/    /'
      ((FAIL++)) || true
    fi
  done
}

# No hardcoded personal paths (tokens are intentional — see config/path-tokens.md)
check_pattern "hardcoded Windows user path" 'C:\\Users\\'
check_pattern "hardcoded Unix home path" '/home/[a-z]'
check_pattern "hardcoded /Users/ path" '/Users/[A-Za-z]'

((FAIL == 0))
