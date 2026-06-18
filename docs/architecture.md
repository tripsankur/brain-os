# Brain OS — Architecture

## Vision

Brain OS is a distributable skill package for Claude Code. It gives your Claude sessions persistent memory (via an Obsidian vault) and structured content pipelines (via modules).

**Current model:** conversation-driven — you invoke `/brain` and module commands in Claude Code sessions. Claude reads skill files, executes pipelines, and writes structured output back to your vault.

**Future model:** frontend UI for end users, with Brain OS handling brain mapping in the background via scheduled workers responding to both time-based triggers and frontend events.

Build path: Brain OS is used to build Brain OS. All architecture decisions are dogfooded through the system before exposing them to end users.

---

## Three agent types

### Type 1 — Subcommand

Human-invoked. Runs inline in the main conversation context.

- **Triggered by:** `/<skill> <subcommand>` in a Claude Code session
- **Executes:** inline — reads files, writes files, may spawn Explore agents for research
- **Scope:** session-scoped, user-driven
- **Examples:** `/brain start`, `/brain diagram social-content`, `/social-content run`
- **Skill files:** `core/subcommands/{name}.md` → installed to `~/.claude/skills/brain/subcommands/`
- **Operational data:** `Claude/` vault layer (workflow, preferences, log, projects-index)

### Type 2 — Pipeline agent

Orchestrator-invoked. Executes one stage of a content or analysis pipeline.

- **Triggered by:** an orchestrator subcommand (e.g. `/social-content run`)
- **Executes:** inline in the same Claude context — **never spawned via `Agent()`**
- **Scope:** run-scoped; reads from and writes to `runs/{run_id}/`
- **Examples:** `sc-research-001`, `sc-draft-001`, `sc-critique-001`, `sc-format-001`
- **Skill files:** `modules/{name}/agents/{agent}.md` → installed to `~/.claude/skills/{name}/agents/`
- **Operational data:** vault `Projects/{name}/agents/{role}/` (PROFILE, WORKLOG, INBOX, OUTBOX, MEMORY)

> **Dual-location pattern:** Agent *definitions* (instructions, prompts, output contracts) live in the `brain-os` repo. Agent *operational data* (run history, memory, inbox/outbox) lives in the vault. The install script wires them at install time by resolving `{{VAULT_PATH}}` tokens.

### Type 3 — Background worker *(future — Tier C)*

Scheduled or event-triggered. Runs without human initiation.

- **Triggered by:** `async: true` Claude Code hook (cron) or frontend event
- **Executes:** autonomously; reports to vault or notifies user
- **Scope:** system-scoped
- **Candidate workers:**
  - `nightly-registry-sync` — runs `/brain sync` across all projects at 02:00
  - `weekly-history-miner` — scans session JSONL logs, surfaces recurring topics and open questions
  - `on-change-diagram-refresh` — when an agent skill file changes, triggers `/brain diagram {project}`
  - `memory-decay-auditor` — flags stale project memories older than 30 days for review
- **Skill files:** `core/workers/` *(not yet created — Tier C)*

---

## Skill definition vs. operational data

Every agent has two halves that live in different places:

| Half | What it contains | Where it lives |
|------|-----------------|----------------|
| Skill definition | Instructions, prompts, output schema, gate conditions | `brain-os` repo → `~/.claude/` on install |
| Operational data | Run history, memory, inbox/outbox, PROFILE | Obsidian vault → `Projects/{name}/` |

The install script resolves `{{VAULT_PATH}}` and `{{CLAUDE_PATH}}` tokens, linking both halves at install time. Reinstalling updates the skill definitions without touching vault data.

---

## Source → install mapping

```
core/brain.md                        → ~/.claude/commands/brain.md
core/subcommands/*.md                → ~/.claude/skills/brain/subcommands/
modules/{name}/{name}.md             → ~/.claude/commands/{name}.md
modules/{name}/agents/*.md           → ~/.claude/skills/{name}/agents/
modules/{name}/agents/_deprecated/   → NOT installed (archived source only)
```

---

## Vault layout

Skills read and write a specific vault structure:

```
<vault>/
  Claude/
    workflow.md          — session protocol (auto-injected via UserPromptSubmit hook)
    preferences.md       — output style, tool preferences
    projects-index.md    — active project registry
    agents.md            — global agent registry
    modules.md           — installed module registry (written by install script)
    log.md               — append-only session log
  Projects/
    {name}/
      {name}.md                — knowledge wiki (Obsidian folder-note)
      {name}-status.md         — current phase, done, next, blockers
      {name}-session-log.md    — append-only session log
      runs/                    — per-run pipeline output artifacts
      agents/
        {role}/
          PROFILE.md           — agent identity and constraints
          MEMORY.md            — durable learnings (promoted via approve)
          INBOX.md             — pending observations for next run
          WORKLOG.md           — run-level activity log
      brands/                  — brand configs (social-content module)
      _brain/                  — module registry, internal metadata
```

---

## Tier roadmap

| Tier | Description | Status |
|------|-------------|--------|
| A | Multi-tenant scoped vault — each project gets isolated namespace | ✅ Done |
| B | Hierarchical brain — orchestrator + pipeline specialists + `/brain` subcommands | ✅ Done (v1) |
| C | Brain as Agent OS — event bus, background workers, frontend interface, cross-agent shared memory | 🎯 Target |
