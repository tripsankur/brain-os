#!/usr/bin/env bash
# Brain OS install script — resolves path tokens and copies skill files to ~/.claude/
# Usage: ./install.sh [--config /path/to/brain-os.config.json] [--dry-run]

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$REPO_ROOT/brain-os.config.json"
DRY_RUN=false
INIT_VAULT=false

for arg in "$@"; do
  case "$arg" in
    --config=*)   CONFIG_FILE="${arg#*=}" ;;
    --config)     shift; CONFIG_FILE="${1:-}" ;;
    --dry-run)    DRY_RUN=true ;;
    --init-vault) INIT_VAULT=true ;;
  esac
done

if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "ERROR: config not found at $CONFIG_FILE"
  echo "Copy config/brain-os.config.example.json to brain-os.config.json and fill in your paths."
  exit 1
fi

# Parse JSON config with bash (avoids Python path issues on Windows/Git Bash)
read_json_string() {
  local key="$1"
  grep -o "\"${key}\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" "$CONFIG_FILE" \
    | sed 's/.*: *"\(.*\)"/\1/'
}

VAULT_PATH=$(read_json_string "vault_path")
CLAUDE_RAW=$(read_json_string "claude_install_path")

# Expand ~ in claude_install_path
CLAUDE_PATH="${CLAUDE_RAW/#\~/$HOME}"

echo "Brain OS Install"
echo "================"
echo "  Repo:   $REPO_ROOT"
echo "  Vault:  $VAULT_PATH"
echo "  Claude: $CLAUDE_PATH"
[[ "$DRY_RUN" == true ]] && echo "  Mode:   DRY RUN (no files written)"
echo ""

# Token resolver — replace {{TOKEN}} placeholders in a file and write to dest.
# Escapes & and \ in replacement values so sed doesn't misinterpret them.
resolve_and_copy() {
  local src="$1"
  local dest="$2"
  if [[ "$DRY_RUN" == true ]]; then
    echo "  [dry-run] $src → $dest"
    return
  fi
  mkdir -p "$(dirname "$dest")"
  # Escape backslashes and ampersands for sed replacement strings
  local vault_esc claude_esc repo_esc
  vault_esc=$(printf '%s\n' "$VAULT_PATH"  | sed 's/[\\&]/\\&/g')
  claude_esc=$(printf '%s\n' "$CLAUDE_PATH" | sed 's/[\\&]/\\&/g')
  repo_esc=$(printf '%s\n'  "$REPO_ROOT"   | sed 's/[\\&]/\\&/g')
  sed -e "s|{{VAULT_PATH}}|${vault_esc}|g" \
      -e "s|{{CLAUDE_PATH}}|${claude_esc}|g" \
      -e "s|{{REPO_PATH}}|${repo_esc}|g" \
      "$src" > "$dest"
  echo "  installed $dest"
}

# Copy a file as-is (no tokens to replace)
copy_file() {
  local src="$1"
  local dest="$2"
  if [[ "$DRY_RUN" == true ]]; then
    echo "  [dry-run] $src → $dest"
    return
  fi
  mkdir -p "$(dirname "$dest")"
  cp "$src" "$dest"
  echo "  installed $dest"
}

echo "Installing brain subcommand..."
resolve_and_copy "$REPO_ROOT/core/brain.md" "$CLAUDE_PATH/commands/brain.md"

echo ""
echo "Installing brain subcommands..."
for f in "$REPO_ROOT/core/subcommands/"*.md; do
  [[ -f "$f" ]] || continue
  name="$(basename "$f")"
  resolve_and_copy "$f" "$CLAUDE_PATH/skills/brain/subcommands/$name"
done

echo ""
echo "Installing modules..."
for module_json in "$REPO_ROOT/modules/"*/module.json; do
  [[ -f "$module_json" ]] || continue
  module_dir="$(dirname "$module_json")"
  module_name=$(grep -o '"name"[[:space:]]*:[[:space:]]*"[^"]*"' "$module_json" \
    | sed 's/.*: *"\(.*\)"/\1/')

  if [[ -z "$module_name" ]]; then
    echo "  WARNING: could not read name from $module_json — skipping"
    continue
  fi

  echo ""
  echo "  [$module_name] orchestrator..."
  resolve_and_copy "$module_dir/$module_name.md" "$CLAUDE_PATH/commands/$module_name.md"

  echo "  [$module_name] agents..."
  for f in "$module_dir/agents/"*.md; do
    [[ -f "$f" ]] || continue
    agent_name="$(basename "$f")"
    copy_file "$f" "$CLAUDE_PATH/skills/$module_name/agents/$agent_name"
  done

  # Register module in vault modules registry
  if [[ -n "$VAULT_PATH" && -d "$VAULT_PATH" ]]; then
    module_version=$(grep -o '"version"[[:space:]]*:[[:space:]]*"[^"]*"' "$module_json" \
      | sed 's/.*: *"\(.*\)"/\1/')
    MODULES_REG="$VAULT_PATH/Claude/modules.md"
    mkdir -p "$(dirname "$MODULES_REG")"
    TODAY=$(date '+%Y-%m-%d')
    if [[ ! -f "$MODULES_REG" ]]; then
      printf '# Installed Modules\n> Auto-managed by install.sh. Do not edit manually.\n\n| module | version | installed | claude_path |\n|--------|---------|-----------|-------------|\n' \
        > "$MODULES_REG"
    fi
    # Remove stale row for this module (handles reinstall), then append fresh row
    grep -v "^| ${module_name} " "$MODULES_REG" > "${MODULES_REG}.tmp" || true
    mv "${MODULES_REG}.tmp" "$MODULES_REG"
    echo "| ${module_name} | ${module_version} | ${TODAY} | ${CLAUDE_PATH} |" >> "$MODULES_REG"
    echo "  [$module_name] registered in $MODULES_REG"
  fi
done

echo ""
echo "Shipping vault templates (so /brain init works without the repo)..."
if [[ -d "$REPO_ROOT/templates" && "$DRY_RUN" == false ]]; then
  mkdir -p "$CLAUDE_PATH/brain-templates"
  cp -R "$REPO_ROOT/templates/." "$CLAUDE_PATH/brain-templates/"
  echo "  templates -> $CLAUDE_PATH/brain-templates"
fi

# Bootstrap a fresh vault skeleton. Idempotent: only copies files that don't exist.
if [[ "$INIT_VAULT" == true || ! -f "$VAULT_PATH/Claude/workflow.md" ]]; then
  echo ""
  echo "Bootstrapping vault skeleton at $VAULT_PATH ..."
  VAULT_TPL="$REPO_ROOT/templates/vault"
  if [[ "$DRY_RUN" == false && -d "$VAULT_TPL" ]]; then
    while IFS= read -r -d '' src; do
      rel="${src#"$VAULT_TPL"/}"
      dest="$VAULT_PATH/$rel"
      if [[ ! -e "$dest" ]]; then
        mkdir -p "$(dirname "$dest")"
        cp "$src" "$dest"
        echo "  + $rel"
      fi
    done < <(find "$VAULT_TPL" -type f -print0)
  fi
  echo "Vault skeleton ready. Add the session-start hook (see README > Session hook) to finish."
fi

echo ""
echo "Done. Brain OS installed to $CLAUDE_PATH"
