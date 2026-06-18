# /brain diagram — Architecture Diagram Generator

Generate or regenerate living Mermaid diagrams from the actual state of skill files and vault structure. Diagrams reflect what the code says, not what was true at last edit.

## Usage

```
/brain diagram [target]
```

| target | What it diagrams |
|--------|-----------------|
| (none) | All targets — full Brain OS + all registered projects |
| `brain` | Brain OS level only — skills map, subcommand table, vault layers |
| `{project-name}` | One project — pipeline flow, agent roster, data flow sequence |

---

## Execution

**Step 1 — Resolve target**

- No argument → targets = `["brain"] + all active projects from Claude/projects-index.md`
- `brain` → targets = `["brain"]`
- `{name}` → verify `{name}` exists in `Claude/projects-index.md`. If not found, halt: "Project '{name}' not in index. Run `/brain new-project {name}` first."

**Step 2 — Explore each target**

For each target, spawn an Explore agent to extract structure from source files. Pass a focused prompt — do not ask the Explore agent to write anything.

**For `brain` target**, prompt the Explore agent:

> Read these files and return structured findings:
> 1. `{{REPO_PATH}}/core/brain.md` — extract the dispatch table (subcommand → file mapping)
> 2. Each subcommand file in `{{REPO_PATH}}/core/subcommands/` — extract: subcommand name, one-line purpose, what vault paths it reads/writes
> 3. `{{VAULT_PATH}}/Claude/projects-index.md` — extract active projects list
> 4. List all module directories in `{{REPO_PATH}}/modules/` — extract module names
>
> Return as structured data: module list, subcommand list with purposes and vault paths, active project list.

**For `{project-name}` target** (e.g. `social-content`), prompt the Explore agent:

> Read these files and return structured findings for the `{project-name}` project:
> 1. The orchestrator skill file for this project — extract: pipeline stage sequence, gate conditions (type + pass criteria + on-fail), subcommands list
> 2. Each agent skill file under `{{REPO_PATH}}/modules/{project-name}/agents/` — extract for each: agent_id, role, input files read, output file written, gate type (hard/quality/blocking/none), status (active/deprecated)
> 3. `{{VAULT_PATH}}/Projects/{project-name}/_brain/registry/agents.md` — extract active agents list
>
> Return as structured data: pipeline sequence, agent list with inputs/outputs/gates, gate summary.

**Step 3 — Render diagrams from Explore output**

Using the structured data returned by the Explore agent, render Mermaid diagrams. Do not invent structure — only render what the Explore agent found.

**For `brain` target**, write `{{VAULT_PATH}}/Claude/diagrams/brain-os.md`:

Content structure:
- `## Skills map` — flowchart showing all modules + their agent counts + vault paths they touch
- `## Subcommand table` — flowchart of /brain subcommands with one-line purpose each
- `## Active projects` — list with phase and last session date
- `## Update log` — append a row: `| {YYYY-MM-DD} | Regenerated from source |`

**For `{project-name}` target**, update the diagrams at `Projects/{project-name}/diagrams/`:

- `pipeline-flow.md` — full flowchart: every active agent in sequence, gates with pass/fail paths, error states
- `agent-roster.md` — agent registry table (from source files, not memory), mindmap of responsibilities

For each diagram file:
- If file exists: update the Mermaid block and append to update log — do not replace the full file, only the diagram block and log row
- If file does not exist: create it with the standard template (header, Mermaid block, gate summary table, update log)

**Step 4 — Report**

```
Diagrams updated:

  brain:
    Claude/diagrams/brain-os.md — {N} subcommands, {N} modules, {N} active projects

  {project-name}:
    Projects/{project-name}/diagrams/pipeline-flow.md — {N} active agents, {N} gates
    Projects/{project-name}/diagrams/agent-roster.md — {N} active, {N} deprecated

All diagrams reflect current source state as of {YYYY-MM-DD}.
```

---

## Design notes

- The Explore agent reads; the orchestrator writes. Explore never touches vault diagram files directly.
- Deprecated agents are included in the roster with ❌ status — they should be visible, not erased.
- Gate conditions are extracted verbatim from the agent skill files — if the file changes, the next `/brain diagram` call picks it up automatically.
- Run this after any pipeline change that affects agent count, gate conditions, or subcommand list.
