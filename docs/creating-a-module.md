# Creating a Brain OS Module

A module is a self-contained skill package — an orchestrator skill file plus pipeline agents. `social-content` is the reference module.

---

## Directory layout

```
modules/{name}/
  module.json        — module metadata (required)
  {name}.md          — orchestrator skill file (required)
  agents/
    *.md             — pipeline agent skill files (inline execution only)
    _deprecated/     — retired agents (not installed, kept for history)
```

The module name must be a lowercase hyphenated slug. The directory name, `module.json` `name` field, and orchestrator filename must all match.

---

## module.json

Every module requires a `module.json` at the root of its directory:

```json
{
  "name": "my-module",
  "version": "0.1.0",
  "description": "One sentence describing what this module does",
  "vault_dir": "Projects/my-module",
  "required_config_keys": ["vault_path", "claude_install_path"]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | yes | Must match directory name and orchestrator filename |
| `version` | yes | Semver string |
| `description` | yes | Single sentence |
| `vault_dir` | yes | Vault subdirectory the module reads/writes (relative to vault root) |
| `required_config_keys` | yes | Config keys the module depends on |

---

## Orchestrator skill file (`{name}.md`)

The orchestrator is the entry point — it handles subcommand dispatch and runs the pipeline. It is installed to `~/.claude/commands/{name}.md` and becomes the `/name` slash command.

Use `{{VAULT_PATH}}` and `{{CLAUDE_PATH}}` tokens wherever paths appear. These are resolved at install time.

**Template:**

```markdown
# /{name} — Short description
<!-- Orchestrator skill. Reads agent files from {{CLAUDE_PATH}}/skills/{name}/agents/. -->

Vault: `{{VAULT_PATH}}/Projects/{name}`

Run the subcommand passed as the first argument. If no argument given, run `status`.

## Subcommand dispatch

| Subcommand | What it does |
|------------|-------------|
| `run`      | Execute the main pipeline |
| `status`   | Show current state |

---

## run

1. Read `{{CLAUDE_PATH}}/skills/{name}/agents/research.md`. Execute its instructions...
```

---

## Pipeline agents (`agents/*.md`)

Agents are **inline execution only** — never spawned via `Agent()`. The orchestrator reads each agent's skill file at runtime and executes the instructions within the current conversation turn.

Agent filenames should follow the `{function}.md` pattern (e.g. `research.md`, `draft.md`).

**What agents can do:**
- Read vault files to gather context
- Write vault files to persist output
- Call tools (Read, Write, Glob, Grep, WebSearch)
- Return structured output for the next stage

**What agents must NOT do:**
- Spawn sub-agents via `Agent()`
- Hardcode any paths — use tokens, or receive paths from the orchestrator
- Access `Personal/` vault directory

---

## Path tokens

| Token | Resolves to | Use it for |
|-------|-------------|------------|
| `{{VAULT_PATH}}` | `config.vault_path` | Any vault file read/write |
| `{{CLAUDE_PATH}}` | `config.claude_install_path` | Reading installed agent skill files |
| `{{REPO_PATH}}` | brain-os repo root | Rarely needed in modules |

All tokens are replaced at install time by `install.sh` / `install.ps1`. No `{{TOKEN}}` syntax should appear in installed files — the `token-scan` CI gate enforces this.

---

## Vault directory ownership

Each module owns a vault directory (`vault_dir` in `module.json`). By convention:

```
<vault>/Projects/{name}/         — main project dir
<vault>/Projects/{name}/runs/    — per-run output artifacts
<vault>/Projects/{name}/agents/  — agent INBOX.md and MEMORY.md files
<vault>/Projects/{name}/brands/  — brand registry (if applicable)
<vault>/Projects/{name}/_brain/  — module registry, internal metadata
```

The module's orchestrator is responsible for creating these directories on first use if they don't exist (or document that `/brain new-project {name}` must be run first).

---

## Installing your module

After adding a module to `modules/`, re-run the install script:

```bash
./install.sh          # bash (macOS/Linux/WSL/Git Bash)
.\install.ps1         # PowerShell (Windows)
```

The install script auto-discovers all modules by scanning `modules/*/module.json` — no manual registration needed.

---

## CI checks

Your module passes the CI gate when:

1. `module-manifest` unit test passes — `module.json` has all required fields, name matches directory
2. `token-scan` passes — no hardcoded paths in any agent or orchestrator file
3. `dispatch-table` passes — all referenced agent paths exist (if your orchestrator references them statically)
