#!/usr/bin/env bash
# E2E test: install.sh resolves tokens and copies files correctly

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FAIL=0

# Create a temp install dir and a test config
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

TEST_VAULT="$TMP/vault"
TEST_CLAUDE="$TMP/claude"
TEST_CONFIG="$TMP/test.config.json"

cat > "$TEST_CONFIG" <<EOF
{
  "vault_path": "$TEST_VAULT",
  "claude_install_path": "$TEST_CLAUDE"
}
EOF

# Run install against temp dirs
bash "$REPO_ROOT/install.sh" --config="$TEST_CONFIG"

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

no_token() {
  local label="$1"
  local file="$2"
  if grep -q '{{' "$file" 2>/dev/null; then
    echo "  FAIL  $label — unresolved {{TOKEN}} found in $file"
    ((FAIL++)) || true
  else
    echo "  PASS  $label"
  fi
}

file_exists() {
  local label="$1"
  local file="$2"
  if [[ -f "$file" ]]; then
    echo "  PASS  $label"
  else
    echo "  FAIL  $label — file missing: $file"
    ((FAIL++)) || true
  fi
}

echo "  --- install file checks ---"

file_exists "brain.md installed"            "$TEST_CLAUDE/commands/brain.md"
file_exists "social-content.md installed"   "$TEST_CLAUDE/commands/social-content.md"
file_exists "start.md subcommand"           "$TEST_CLAUDE/skills/brain/subcommands/start.md"
file_exists "diagram.md subcommand"         "$TEST_CLAUDE/skills/brain/subcommands/diagram.md"
file_exists "research agent installed"      "$TEST_CLAUDE/skills/social-content/agents/research.md"
file_exists "critique agent installed"      "$TEST_CLAUDE/skills/social-content/agents/critique.md"

echo "  --- token resolution checks ---"

check "brain.md vault path resolved"        "$TEST_CLAUDE/commands/brain.md"            "$TEST_VAULT"
check "brain.md claude path resolved"       "$TEST_CLAUDE/commands/brain.md"            "$TEST_CLAUDE"
check "social-content.md vault resolved"    "$TEST_CLAUDE/commands/social-content.md"   "$TEST_VAULT"
check "social-content.md claude resolved"   "$TEST_CLAUDE/commands/social-content.md"   "$TEST_CLAUDE"
check "diagram.md repo path resolved"       "$TEST_CLAUDE/skills/brain/subcommands/diagram.md" "$REPO_ROOT"
check "history.md claude path resolved"     "$TEST_CLAUDE/skills/brain/subcommands/history.md" "$TEST_CLAUDE"

no_token "brain.md no unresolved tokens"        "$TEST_CLAUDE/commands/brain.md"
no_token "social-content.md no unresolved tokens" "$TEST_CLAUDE/commands/social-content.md"
no_token "diagram.md no unresolved tokens"      "$TEST_CLAUDE/skills/brain/subcommands/diagram.md"

echo "  --- deprecated agents not installed ---"

if [[ -f "$TEST_CLAUDE/skills/social-content/agents/cto-review.md" ]]; then
  echo "  FAIL  deprecated cto-review.md should not be installed"
  ((FAIL++)) || true
else
  echo "  PASS  deprecated agents not installed"
fi

((FAIL == 0))
