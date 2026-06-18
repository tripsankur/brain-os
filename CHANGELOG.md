# Changelog

All notable changes to Brain OS will be documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

---

## [Unreleased] — v0.1.0

### Added
- Core `/brain` skill subcommands: start, end, capture, ingest, history, status, new-project, recall, agent-register, route, promote, sync, diagram, **map, agenda, rename**
- **Journal / Map / Hands model** (`docs/brain-graphify-loops.md`): the vault is the journal, graphify is the optional map, agenda + loops are the hands
- **`/brain map`** — graphify-backed knowledge graph over **code + vault notes in one corpus** (single-corpus staging so code↔intent cross-edges form; verified). Optional dependency, scoped to this one command. Central graph cache.
- **`/brain agenda`** — prioritized per-project backlog (`{name}-agenda.md`) that `/loop` and Tier-C workers consume
- **`/brain rename`** — rename a project across the whole vault (folder, prefixed files, wikilinks, index) + the code-side coupling steps
- `social-content` module: 4-agent pipeline (research → draft → critique → format → approval)
- Config system: `brain-os.config.json` with vault path, endpoint, per-operation model selection
- Install scripts: `install.sh` and `install.ps1`
- Test suite: dispatch table integrity, registry schema, vault scaffolding, e2e install
- GitHub Actions CI

### Fixed
- **Naming drift**: `start`/`end`/`status`/`new-project`/`recall` now use the PREFIXED folder-note names (`{name}-status.md`, `{name}.md`) — they previously read/wrote unprefixed files that never existed, so writes were silently unrecalled.
- **`sync` is now the structural projector**: auto-indexes loose notes into `{name}.md` (`## Documents`), flags dated snapshots for `_archive/`, checks the canonical set — additive + idempotent. Runs at `/brain end` so structure doesn't depend on write-discipline.
- `install.ps1` non-ASCII parse bug (em-dash) that broke the installer under Windows PowerShell 5.1.

---
