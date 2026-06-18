#!/usr/bin/env bash
# Verify every module under modules/ has a valid module.json with required fields.
# Required fields: name, version, description, vault_dir, required_config_keys

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MODULES_DIR="$REPO_ROOT/modules"
FAIL=0

if [[ ! -d "$MODULES_DIR" ]]; then
  echo "  SKIP: modules/ directory not found"
  exit 0
fi

REQUIRED_FIELDS=("name" "version" "description" "vault_dir" "required_config_keys")

for module_json in "$MODULES_DIR"/*/module.json; do
  [[ -f "$module_json" ]] || continue
  module_dir="$(dirname "$module_json")"
  dir_name="$(basename "$module_dir")"

  for field in "${REQUIRED_FIELDS[@]}"; do
    if ! grep -q "\"${field}\"" "$module_json"; then
      echo "  MISSING field '$field' in $module_json"
      ((FAIL++)) || true
    fi
  done

  # name in module.json must match directory name
  json_name=$(grep -o '"name"[[:space:]]*:[[:space:]]*"[^"]*"' "$module_json" \
    | sed 's/.*: *"\(.*\)"/\1/')
  if [[ "$json_name" != "$dir_name" ]]; then
    echo "  NAME MISMATCH: module.json name='$json_name' but dir='$dir_name' in $module_json"
    ((FAIL++)) || true
  fi

  # orchestrator skill file must exist: modules/{name}/{name}.md
  if [[ ! -f "$module_dir/$dir_name.md" ]]; then
    echo "  MISSING orchestrator: modules/$dir_name/$dir_name.md"
    ((FAIL++)) || true
  fi
done

((FAIL == 0))
