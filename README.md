# Brain OS

A conversation-driven **memory + automation OS** for [Claude Code](https://claude.com/claude-code).
Brain OS turns a plain Markdown vault (Obsidian-friendly) into a persistent, multi-project memory
layer, and gives the assistant a set of composable `/brain` commands that maintain state, recall
context, and drive work across sessions — without relying on the assistant *remembering* to do the
right thing. Structure is a property of the system, projected deterministically from the
filesystem.

## The model: Journal · Map · Hands

| Layer | Engine | Owns |
|-------|--------|------|
| **Journal** | Markdown vault (Obsidian) | intent, decisions, status, session log, preferences, agenda |
| **Map** | [graphify](https://graphifylabs.ai/) *(optional)* | code + notes as one queryable knowledge graph |
| **Hands** | loops / agenda | execute tasks against a project's prioritized backlog |

- **Structured recall** (a project's status / next steps / decisions) = direct file reads. Cheap, deterministic, always fresh.
- **Associative recall** ("what across all my work relates to X") = the optional graphify Map.
- **No write-discipline required**: write freely; `/brain sync` projects structure (indexes loose notes, repairs links) and runs at `/brain end`.

## Prerequisites

- **Claude Code** (the CLI/agent).
- A Markdown vault directory (Obsidian recommended for the graph view, not required).
- **PowerShell** (Windows) or **bash** (macOS/Linux) for the installer.
- *Optional:* **Python ≥3.10 + `graphifyy`** — required **only** for `/brain map` (the code/associative graph). Everything else works with zero extra dependencies.

## Install

```bash
git clone <your-fork-url> brain-os && cd brain-os
cp config/brain-os.config.example.json brain-os.config.json
# edit brain-os.config.json: set vault_path and claude_install_path
./install.sh            # macOS/Linux
# or on Windows:
powershell -File install.ps1
```

The installer resolves path tokens (`{{VAULT_PATH}}`, `{{CLAUDE_PATH}}`, `{{REPO_PATH}}`) from your
config and copies the skill files into your Claude install — **no hardcoded user paths** (verified:
a clean install leaves zero unresolved tokens). To re-point Brain OS at a different machine/vault,
edit the config and re-run the installer.

## Commands

| Command | Does |
|---------|------|
| `/brain start` | Load active-project status + top agenda items; process inbox |
| `/brain end` | Write session back (session-log, status, decisions, agenda) + run `sync --fix` |
| `/brain status` | Health check across projects |
| `/brain new-project [name]` | Scaffold a project's canonical file set |
| `/brain capture` | Save a session insight as a linked note |
| `/brain recall {topic}` | Surface connected context (wiki + decisions + captures) |
| `/brain agenda [proj] [next\|add\|done…]` | The prioritized backlog loops consume |
| `/brain map [proj]` | Build/query the graphify knowledge graph (code + notes) — *needs graphify* |
| `/brain sync [--fix]` | Project structure from the filesystem: index loose notes, repair links, check completeness |
| `/brain rename {old} {new}` | Rename a project across the vault (+ reports the code-side steps) |
| `/brain diagram`, `/brain ingest`, `/brain promote`, `/brain route`, `/brain agent-register` | see `core/subcommands/` |

## Conventions (the canonical layout)

Each project is a folder under `Projects/{name}/` using the **prefixed folder-note** pattern, so every
note is identifiable in the graph view:

```
Projects/{name}/
  {name}.md                # wiki root (folder note)
  {name}-status.md         # Current (Phase/Done/Next Steps/Blocked By) + History
  {name}-session-log.md    # append-only: ## [YYYY-MM-DD] | summary
  {name}-decisions.md      # append-only: ## [date] Decision: X | Rationale: Y
  {name}-agenda.md         # prioritized backlog (todo/doing/done/blocked)
  {name}-code-map.md       # pointer to the graphify graph (if built)
  captures/                # captured insights + captures.md hub
  _archive/                # dated snapshots (excluded from the active graph)
```

`/brain sync` enforces this set and auto-indexes any loose note into `{name}.md` — orphans become
impossible by construction.

## Modules

Brain OS is extensible via modules (e.g. `social-content`). A module ships its own orchestrator +
agents and registers on install. See `docs/creating-a-module.md`.

## Documentation

- `docs/brain-graphify-loops.md` — the Journal/Map/Hands architecture + agenda/loops design
- `docs/architecture.md` — agent taxonomy + tiers
- `docs/creating-a-module.md` — module spec
- `CONTRIBUTING.md` — how to contribute
- `RELEASE-CHECKLIST.md` — pre-public scrub + release steps

## Development

```bash
./tests/run-all.sh          # unit + e2e (no real vault needed — uses fixtures)
./tests/unit/token-scan.sh  # gate: no hardcoded paths / unresolved tokens
```

## License

MIT — see [LICENSE](LICENSE).
