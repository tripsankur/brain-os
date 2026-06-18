# Brain OS

> **Pre-release (P0)** — Core skill files and install scripts are being migrated in this phase. Commands listed below work on the author's machine; portable install (`install.sh` / `install.ps1`) is P0 deliverable, not yet available. Watch the repo or check the [Roadmap](#roadmap) for progress.

A conversation-driven memory and agent system for [Claude Code](https://claude.ai/code). Brain OS turns your Obsidian vault into a persistent, multi-project memory layer and gives Claude a set of orchestrated commands (`/brain`, `/social-content`, and more) that compose agents, route by operation type, and maintain state across sessions.

---

## What it does

- **Persistent memory**: Session start/end hooks automatically read and write your vault so Claude always knows project status, recent decisions, and active context.
- **Multi-project routing**: One `/brain` command dispatches to specialized subcommands — status, capture, diagram, agent-register, and more.
- **Model routing by operation** *(P2)*: Critique-heavy work routes to Opus; formatting and recall route to Haiku. Model assignments are declared in `brain-os.config.json` — wiring them end-to-end is a P2 milestone.
- **Agent pipelines**: Complex workflows (e.g., social content generation) run as inline pipeline agents coordinated by a single skill file.
- **Vault-portable**: All skill files use path tokens (`{{VAULT_PATH}}`, `{{CLAUDE_PATH}}`). The install script resolves them from your config — no hardcoded user paths.

---

## Prerequisites

- Claude Code (CLI or desktop app)
- [Obsidian](https://obsidian.md/) with a vault you own
- bash (macOS/Linux/WSL) or PowerShell (Windows)

---

## Install

> **P0 status** — `install.sh` / `install.ps1` are not yet written. The steps below describe the intended flow once P0 is complete.

**macOS / Linux / WSL:**
```bash
git clone https://github.com/ankurtripathi/brain-os.git  # repo is currently private
cd brain-os
cp config/brain-os.config.example.json config/brain-os.config.json
# Edit config/brain-os.config.json with your vault path and preferences
./install.sh
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/ankurtripathi/brain-os.git
cd brain-os
cp config\brain-os.config.example.json config\brain-os.config.json
# Edit config\brain-os.config.json with your vault path and preferences
.\install.ps1
```

The install script will:
1. Read `config/brain-os.config.json`
2. Resolve `{{TOKEN}}` placeholders in all skill files
3. Copy `core/` → `~/.claude/commands/` and `~/.claude/skills/`
4. Copy `modules/` → `~/.claude/commands/` and `~/.claude/skills/`

After install, add the `UserPromptSubmit` hook to `~/.claude/settings.json` manually (see [Configuration](#configuration)).

---

## Configuration

`config/brain-os.config.json` (not committed — copy from example):

```json
{
  "vault_path": "/path/to/your/obsidian/vault",
  "claude_install_path": "~/.claude",
  "models": {
    "default": "claude-sonnet-4-6",
    "critique": "claude-opus-4-7",
    "format": "claude-haiku-4-5-20251001",
    "recall": "claude-haiku-4-5-20251001",
    "diagram": "claude-sonnet-4-6"
  }
}
```

The `models` block declares which model handles each operation type. This config is read at install time today (token substitution); runtime model dispatch is wired in P2.

See `config/path-tokens.md` for all supported `{{TOKEN}}` values.

---

## Quickstart

After install, open Claude Code in any directory and type:

```
/brain status
```

This reads your vault's active projects and surfaces what's in progress. Then try:

```
/brain start
```

To begin a tracked session with context loaded from vault.

---

## Available commands

| Command | What it does |
|---------|-------------|
| `/brain status` | Show active projects and current context from vault |
| `/brain start` | Begin a session — loads project status into context |
| `/brain end` | Close session — writes summary to vault log |
| `/brain capture` | Save an insight, decision, or note to vault |
| `/brain recall` | Search vault for relevant context |
| `/brain diagram` | Generate a Mermaid diagram of a module |
| `/brain new-project` | Scaffold a new project in vault |
| `/brain agent-register` | Add an agent entry to the registry |
| `/brain route` | Route a task to the right agent or module |
| `/brain promote` | Move a draft or idea to active project status |
| `/brain sync` | Sync vault index and project list |
| `/brain history` | Show session history for a project |
| `/social-content` | Run the social content pipeline (research → draft → critique → format) |

---

## Modules

Brain OS is organized into modules under `modules/`. Each module is a self-contained pipeline with its own agents, prompts, and registry.

| Module | Status | Description |
|--------|--------|-------------|
| `social-content` | Active | 4-agent pipeline: research, draft, critique (with 5-part review), format |

---

## Vault structure expected

Brain OS reads from and writes to a specific vault layout:

```
<vault>/
  Claude/
    workflow.md          # loaded on every session start
    preferences.md       # loaded on every session start
    projects-index.md    # loaded on every session start
    agents.md            # global agent registry
  Projects/
    <project-name>/
      <project-name>.md          # project wiki (main note)
      <project-name>-status.md   # current phase, done, blockers, next
      <project-name>-session-log.md
```

If your vault doesn't have this structure, run `/brain new-project <name>` to scaffold it.

---

## Roadmap

| Tier | Milestone | Status |
|------|-----------|--------|
| A | Multi-tenant vault memory, session hooks | ✅ Done |
| B | Hierarchical `/brain` + specialist modules | ✅ Done |
| P0 | Repo publishable: tokens, install script, tests, README | 🔨 In progress |
| P1 | Migrate all skills to `core/` with token resolution | Planned |
| P2 | Multi-model routing wired end-to-end | Planned |
| C | Background workers via `async: true` hooks, event bus | Future |

---

## Development

```bash
# Run unit tests (fast, no vault needed)
./tests/run-all.sh --unit

# Check for hardcoded paths or unresolved tokens
./tests/unit/token-scan.sh

# Validate dispatch table points to real files
./tests/unit/dispatch-table.sh
```

CI runs on every push to `main`. The token-scan gate blocks any commit with hardcoded user paths in `core/` or `modules/`.

---

## License

MIT — see [LICENSE](LICENSE).
