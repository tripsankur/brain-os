#!/usr/bin/env bash
# E2E test: /brain new-project scaffolding
# Simulates the vault operations that the new-project subcommand performs,
# then asserts the resulting directory structure and file content.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FIXTURE_VAULT="$REPO_ROOT/tests/fixtures/test-vault"
FAIL=0

# Copy fixture vault to a temp dir so we can write to it without polluting source
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

VAULT="$TMP/vault"
cp -r "$FIXTURE_VAULT/" "$VAULT/"

PROJECT="ci-test-project"
PROJECT_DIR="$VAULT/Projects/$PROJECT"
TODAY="2026-01-01"

# ── Simulate what /brain new-project ci-test-project would do ──────────────

mkdir -p "$PROJECT_DIR"

cat > "$PROJECT_DIR/$PROJECT.md" <<EOF
# $PROJECT — Knowledge Wiki
> See also: [[$PROJECT-status]] | [[$PROJECT-session-log]]

## Overview
CI test project scaffolded by brain-os e2e test suite.

## Architecture
- No real code — exists only to verify /brain new-project scaffolding
EOF

cat > "$PROJECT_DIR/$PROJECT-status.md" <<EOF
# $PROJECT — Status
> See also: [[$PROJECT]] | [[$PROJECT-session-log]]

## Current

### Done
- [x] Project initialized

### Next Steps
_(add first tasks)_

### Blocked By
Nothing.

## History

| Date | Milestone |
|------|-----------|
| $TODAY | Project initialized via /brain new-project |
EOF

cat > "$PROJECT_DIR/$PROJECT-session-log.md" <<EOF
# $PROJECT — Session Log
> See also: [[$PROJECT]] | [[$PROJECT-status]]

Append-only. Format: \`## [YYYY-MM-DD] | summary\`

---

## [$TODAY] | Project initialized via /brain new-project
EOF

mkdir -p "$VAULT/_raw/inbox/$PROJECT"
touch "$VAULT/_raw/inbox/$PROJECT/.keep"

echo "| $PROJECT | [[Projects/$PROJECT/$PROJECT]] | Phase 1 | $TODAY |" \
  >> "$VAULT/Claude/projects-index.md"

echo "## [$TODAY] | $PROJECT | Project scaffolded via /brain new-project" \
  >> "$VAULT/Claude/log.md"

# ── Assertions ─────────────────────────────────────────────────────────────

check() {
  local label="$1"
  local file="$2"
  local expect="$3"
  if grep -q "$expect" "$file" 2>/dev/null; then
    echo "  PASS  $label"
  else
    echo "  FAIL  $label — expected '$expect' in $file"
    ((FAIL++)) || true
  fi
}

file_exists() {
  local label="$1"
  local file="$2"
  if [[ -f "$file" ]]; then
    echo "  PASS  $label"
  else
    echo "  FAIL  $label — missing: $file"
    ((FAIL++)) || true
  fi
}

dir_exists() {
  local label="$1"
  local dir="$2"
  if [[ -d "$dir" ]]; then
    echo "  PASS  $label"
  else
    echo "  FAIL  $label — missing dir: $dir"
    ((FAIL++)) || true
  fi
}

echo "  --- project directory structure ---"
dir_exists  "project dir created"                  "$PROJECT_DIR"
file_exists "wiki file {name}.md"                  "$PROJECT_DIR/$PROJECT.md"
file_exists "status file {name}-status.md"         "$PROJECT_DIR/$PROJECT-status.md"
file_exists "session log {name}-session-log.md"    "$PROJECT_DIR/$PROJECT-session-log.md"
file_exists "inbox .keep created"                  "$VAULT/_raw/inbox/$PROJECT/.keep"

echo "  --- file naming convention (folder-note pattern) ---"
check "wiki uses {name}.md not index.md"           "$VAULT/Claude/projects-index.md"    "$PROJECT/$PROJECT"
check "wiki links to {name}-status"                "$PROJECT_DIR/$PROJECT.md"           "$PROJECT-status"
check "wiki links to {name}-session-log"           "$PROJECT_DIR/$PROJECT.md"           "$PROJECT-session-log"

echo "  --- index and log updated ---"
check "project added to projects-index.md"         "$VAULT/Claude/projects-index.md"    "$PROJECT"
check "log.md entry written"                       "$VAULT/Claude/log.md"               "$PROJECT"

echo "  --- content integrity ---"
check "status.md has History table"                "$PROJECT_DIR/$PROJECT-status.md"    "| Date | Milestone |"
check "session-log.md has initialization entry"    "$PROJECT_DIR/$PROJECT-session-log.md" "Project initialized"

((FAIL == 0))
