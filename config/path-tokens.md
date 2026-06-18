# Path Tokens

The install script replaces these tokens in all skill files during installation.
No hardcoded paths are committed to the repo.

| Token | Resolved from config | Example |
|-------|---------------------|---------|
| `{{VAULT_PATH}}` | `config.vault_path` | `/Users/jane/Documents/MyVault` |
| `{{CLAUDE_PATH}}` | `config.claude_install_path` | `~/.claude` |
| `{{REPO_PATH}}` | Directory where install script is run from | `/Users/jane/brain-os` |
| `{{MODEL_DEFAULT}}` | `config.models.default` | `claude-sonnet-4-6` |
| `{{MODEL_CRITIQUE}}` | `config.models.critique` | `claude-opus-4-7` |
| `{{MODEL_FORMAT}}` | `config.models.format` | `claude-haiku-4-5-20251001` |

## Rules

- Every file under `core/` and `modules/` that references a path MUST use tokens.
- The P1 gate check: `grep -r "Users\|home\|C:\\\\" core/ modules/` must return nothing.
- CI runs this check on every push.
