# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Brain OS is a distributable Claude Code skill package. It installs `/brain` and module commands (e.g. `/social-content`) into a user's `~/.claude/` by resolving path tokens from a local config. No code runs at build time — all files are markdown skill instructions read by Claude at runtime.

## Running tests

```bash
# Fast unit tests only (no install, no vault needed)
./tests/run-all.sh --unit

# Full suite (runs install against temp fixtures)
./tests/run-all.sh

# Single test
bash tests/unit/dispatch-table.sh
bash tests/unit/token-scan.sh
```

CI runs `--unit` only (no vault available). E2E tests require `bash` — not PowerShell.

## Install

```bash
cp config/brain-os.config.example.json brain-os.config.json
# Edit brain-os.config.json with vault_path and claude_install_path
./install.sh          # bash (macOS/Linux/WSL/Git Bash)
.\install.ps1         # PowerShell (Windows)
```

`brain-os.config.json` is gitignored — never commit it. After editing `core/` or `modules/`, re-run install to push changes to `~/.claude/`.

## Architecture

### Token system

Every file in `core/` and `modules/` uses path tokens instead of hardcoded paths:

| Token | Resolves to |
|-------|-------------|
| `{{VAULT_PATH}}` | `config.vault_path` |
| `{{CLAUDE_PATH}}` | `config.claude_install_path` |
| `{{REPO_PATH}}` | directory where install script runs |

The install script (`install.sh` / `install.ps1`) resolves tokens via `sed` substitution on copy. **No `{{TOKEN}}` syntax should appear in installed files** — the token-scan CI gate enforces this.

### Source → install mapping

```
core/brain.md                        → ~/.claude/commands/brain.md
core/subcommands/*.md                → ~/.claude/skills/brain/subcommands/
modules/{name}/{name}.md             → ~/.claude/commands/{name}.md
modules/{name}/agents/*.md           → ~/.claude/skills/{name}/agents/
modules/{name}/agents/_deprecated/   → NOT installed (archived source only)
```

### Three agent types

- **Type 1 — Subcommand**: human-invoked (`/brain start`). Skill files live in `core/subcommands/`.
- **Type 2 — Pipeline agent**: orchestrator-invoked inline within a module run. Skill files live in `modules/{name}/agents/`. Never spawned via `Agent()` — always executed inline.
- **Type 3 — Background worker**: scheduled via `async: true` hooks. Not yet built (Tier C).

### Module structure

Each module under `modules/` is self-contained:
```
modules/{name}/
  {name}.md          # orchestrator skill: subcommand dispatch, pipeline stages
  agents/
    *.md             # pipeline agent skill files (inline execution only)
    _deprecated/     # retired agents — kept for history, not installed
```

The orchestrator reads agent files at runtime via `{{CLAUDE_PATH}}/skills/{name}/agents/{agent}.md`.

### Vault layout (expected by skills)

Skills read/write a specific vault structure. The vault path is always `{{VAULT_PATH}}` in source:

```
<vault>/Claude/           # global layer: workflow.md, preferences.md, projects-index.md, agents.md
<vault>/Projects/{name}/  # per-project: {name}.md, {name}-status.md, {name}-session-log.md
```

For social-content specifically: `<vault>/Projects/social-content/` with `runs/`, `agents/`, `brands/`, `_brain/` subdirectories.

## CI gate rules

- `core/` and `modules/` must contain zero hardcoded user paths (`C:\Users\`, `/Users/`, `/home/`)
- `_deprecated/` is excluded from token-scan
- `core/brain.md` dispatch table must reference only files that exist in `core/subcommands/`
