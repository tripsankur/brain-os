# /brain — Obsidian Memory System
<!-- CANONICAL SOURCE — install to ~/.claude/commands/brain.md and subcommands to ~/.claude/skills/brain/subcommands/ -->

Vault: `{{VAULT_PATH}}`

Read the subcommand file for the subcommand passed as `$ARGUMENTS` and execute it. If no argument given, run `status`.

**Dispatch table** — read the file at the path shown, then execute its instructions:

| Subcommand | File |
|------------|------|
| `init` | `{{CLAUDE_PATH}}/skills/brain/subcommands/init.md` |
| `start` | `{{CLAUDE_PATH}}/skills/brain/subcommands/start.md` |
| `end` | `{{CLAUDE_PATH}}/skills/brain/subcommands/end.md` |
| `capture` | `{{CLAUDE_PATH}}/skills/brain/subcommands/capture.md` |
| `ingest` | `{{CLAUDE_PATH}}/skills/brain/subcommands/ingest.md` |
| `history` | `{{CLAUDE_PATH}}/skills/brain/subcommands/history.md` |
| `status` | `{{CLAUDE_PATH}}/skills/brain/subcommands/status.md` |
| `new-project` | `{{CLAUDE_PATH}}/skills/brain/subcommands/new-project.md` |
| `recall` | `{{CLAUDE_PATH}}/skills/brain/subcommands/recall.md` |
| `agent-register` | `{{CLAUDE_PATH}}/skills/brain/subcommands/agent-register.md` |
| `route` | `{{CLAUDE_PATH}}/skills/brain/subcommands/route.md` |
| `promote` | `{{CLAUDE_PATH}}/skills/brain/subcommands/promote.md` |
| `sync` | `{{CLAUDE_PATH}}/skills/brain/subcommands/sync.md` |
| `diagram` | `{{CLAUDE_PATH}}/skills/brain/subcommands/diagram.md` |
| `map` | `{{CLAUDE_PATH}}/skills/brain/subcommands/map.md` (graphify-backed code graph) |
| `agenda` | `{{CLAUDE_PATH}}/skills/brain/subcommands/agenda.md` |
| `rename` | `{{CLAUDE_PATH}}/skills/brain/subcommands/rename.md` |

If the subcommand is not in the table, report: "Unknown subcommand '{arg}'. Available: init, start, end, capture, ingest, history, status, new-project, recall, agent-register, route, promote, sync, diagram, map, agenda, rename"
