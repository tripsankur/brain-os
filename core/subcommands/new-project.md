## new-project {name}

Scaffold a new project in the vault. Run this right after `/init` to link a repo to the brain.

**Detect project name** (use the name passed after `new-project` if provided, otherwise auto-detect):
1. Check `package.json` → `name` field
2. Check `pyproject.toml` → `[project] name`
3. Check `go.mod` → last segment of module path
4. Fallback: basename of current working directory
5. Sanitize: lowercase, hyphens only (e.g. `My App` → `my-app`)

**Check if already exists**: try to Read `{vault}/Projects/{name}/{name}-status.md` — if found, report "Already in vault" and stop.

> **Naming convention (canonical):** every project file is PREFIXED with the project name. The wiki root is `{name}.md` (NOT `index.md`). Files: `{name}.md`, `{name}-status.md`, `{name}-session-log.md`, `{name}-decisions.md`, `{name}-agenda.md`, plus a `captures/` folder. The read/recall/status/start subcommands all expect these exact names.

**Read context from repo** (for richer initial wiki):
- Read `CLAUDE.md` if present — extract architecture summary and purpose
- Read `README.md` if present — extract description

**Scaffold vault project**:

1. Write `{vault}/Projects/{name}/{name}.md` (the wiki root):
   ```markdown
   # {Name} — Knowledge Wiki
   > See also: [[{name}-status]] | [[{name}-decisions]] | [[{name}-session-log]] | [[{name}-agenda]]

   ## Overview
   {1–2 sentence description from CLAUDE.md or README, or "(add description)"}

   ## Architecture
   {3–5 bullets from CLAUDE.md architecture section, or "(add as it emerges)"}

   ## Domain Concepts
   _(add as they emerge)_

   ## Decisions
   See [[{name}-decisions]]
   ```

2. Write `{vault}/Projects/{name}/{name}-status.md`:
   ```markdown
   # {Name} — Status
   > See also: [[{name}]] | [[{name}-decisions]] | [[{name}-session-log]] | [[{name}-agenda]]
   > Overwrite the "## Current" section each session. Preserve "## History".

   ## Current

   **Phase:** Phase 1 — initialized

   ### Done
   - [x] Project initialized

   ### Next Steps
   _(add first tasks)_

   ### Blocked By
   Nothing.

   ## History
   | Date | Milestone |
   |------|-----------|
   | {today} | Project initialized via /brain new-project |
   ```

3. Write `{vault}/Projects/{name}/{name}-decisions.md`:
   ```markdown
   # {Name} — Decisions
   > See also: [[{name}]] | [[{name}-status]] | [[{name}-session-log]]

   Append-only. Format: `## [YYYY-MM-DD] Decision: X | Rationale: Y`

   ---
   ```

4. Write `{vault}/Projects/{name}/{name}-session-log.md`:
   ```markdown
   # {Name} — Session Log
   > See also: [[{name}]] | [[{name}-status]] | [[{name}-decisions]]

   Append-only. Format: `## [YYYY-MM-DD] | summary` (one-line header, optional bullets under it)

   ---

   ## [{today}] | Project initialized via /brain new-project
   ```

5. Write `{vault}/Projects/{name}/{name}-agenda.md` (see the `agenda` subcommand for the schema):
   ```markdown
   # {Name} — Agenda
   > See also: [[{name}]] | [[{name}-status]] | [[{name}-session-log]]
   > Prioritized backlog. `/brain agenda` and `/loop` pull the top `todo`. Move finished items to Done.

   ## Active
   | ID | Pri | Task | Status | Acceptance |
   |----|-----|------|--------|------------|

   ## Done
   ```

6. Write `captures/captures.md` hub at `{vault}/Projects/{name}/captures/captures.md`:
   ```markdown
   # {Name} — Captures
   > [[{name}]] | [[{name}-session-log]]
   > Append-only index of captured insights.

   | Date | Title | Slug |
   |------|-------|------|
   ```

7. Write `.keep` to `{vault}/_raw/inbox/{name}/.keep`

8. Append row to `{vault}/Claude/projects-index.md` Active Projects table:
   ```
   | {Name} | [[Projects/{name}/{name}]] | Phase 1 | {today} |
   ```

9. Append to `{vault}/Claude/log.md`:
   ```
   ## [{today}] | {name} | Project scaffolded via /brain new-project
   ```

10. **Write the pointer into the repo** — run the `pointer` subcommand logic for `{name}` (the
    working dir is the repo root here). It gitignores then writes `CLAUDE.local.md` with the vault
    + code-graph pointers so any agent opening the repo finds the project's memory. Skip only if
    there is no code repo (vault-only project).

Report: "Project {name} created in vault. Inbox at _raw/inbox/{name}/. Pointer written to CLAUDE.local.md (gitignored). Run /brain start to load context."
