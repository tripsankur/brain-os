#!/usr/bin/env bash
# Verify agents.md registry files match expected schema
# Required columns: agent_id | role | status | created | model

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_VAULT="$REPO_ROOT/tests/fixtures/test-vault"
FAIL=0

check_registry() {
  local file="$1"
  local required_cols=("agent_id" "role" "status" "created" "model")

  if [[ ! -f "$file" ]]; then
    echo "  SKIP: $file not found (fixture not yet created)"
    return 0
  fi

  # Check header row contains all required columns
  header=$(grep "^|" "$file" | head -1)
  for col in "${required_cols[@]}"; do
    if ! echo "$header" | grep -q "$col"; then
      echo "  MISSING column '$col' in: $file"
      ((FAIL++))
    fi
  done
}

# Check test fixture registries if they exist
check_registry "$TEST_VAULT/Claude/agents.md"

[[ "$FAIL" -eq 0 ]]
