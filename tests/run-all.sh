#!/usr/bin/env bash
# Brain OS test runner
# Usage: ./tests/run-all.sh [--unit]

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT_ONLY=false
PASS=0
FAIL=0

for arg in "$@"; do
  [[ "$arg" == "--unit" ]] && UNIT_ONLY=true
done

run_test() {
  local name="$1"
  local file="$2"
  if bash "$file"; then
    echo "  PASS  $name"
    ((PASS++)) || true
  else
    echo "  FAIL  $name"
    ((FAIL++)) || true
  fi
}

echo ""
echo "Brain OS Test Suite"
echo "==================="
echo ""
echo "Unit tests:"
run_test "dispatch-table integrity"       "$REPO_ROOT/tests/unit/dispatch-table.sh"
run_test "registry schema"                "$REPO_ROOT/tests/unit/registry-schema.sh"
run_test "token scan (no hardcoded paths)" "$REPO_ROOT/tests/unit/token-scan.sh"
run_test "module manifest"                "$REPO_ROOT/tests/unit/module-manifest.sh"

if [[ "$UNIT_ONLY" == false ]]; then
  echo ""
  echo "E2E tests:"
  run_test "install script"         "$REPO_ROOT/tests/e2e/install.sh"
  run_test "new-project scaffolding" "$REPO_ROOT/tests/e2e/new-project.sh"
fi

echo ""
echo "---"
echo "Results: $PASS passed, $FAIL failed"
echo ""

[[ "$FAIL" -eq 0 ]]
