## pointer [project]

Write/refresh the **brain-managed pointer block** in the repo's `CLAUDE.md` — the durable
breadcrumb that tells any agent (or a fresh Claude session) opening this repo *where this project's
memory lives*: the vault journal (intent) and the graphify code graph (map). This is the one place
where Brain OS writes into the code repo, and it touches **only** a sentinel-delimited block —
never the hand-written rest of the file.

## Usage

```
/brain pointer [project]            # write/refresh the managed block (create CLAUDE.md if absent)
/brain pointer [project] --dry-run  # print the block + what would change; write nothing
```

- `project` defaults to the project resolved from the working directory (see Step 1). Pass it
  explicitly when the repo dir name ≠ the vault folder name.
- Run it from **inside the repo** — repo root is resolved from the working directory.

## Why this exists

`CLAUDE.md` is the file an agent reads first when it starts working in a repo. Without a pointer,
the agent has no idea a Brain OS vault or a graphify graph exists for this project. This block is
that pointer, kept current automatically by `new-project` and `end` (and on demand here). Brain
owns the block; everything outside the markers stays yours.

## Execution

### Step 1 — Resolve project + repo root
- **Repo root** = the working directory (confirm with the user if it's not obviously a repo root,
  same as `map.md` does).
- **Project name** `{name}`:
  1. If `project` was passed, use it.
  2. Else take the repo dir basename and check `{{VAULT_PATH}}/Projects/{basename}/`.
  3. If that folder does NOT exist, the dir name ≠ the vault folder (this is real — e.g. repo
     `Trading-Indicator-SMC/` maps to vault `Projects/SMC-Research/`). Ask the user which vault
     project this repo belongs to, or list `Projects/` and let them pick.
- Confirm `{{VAULT_PATH}}/Projects/{name}/` exists. If not: "run `/brain new-project` first" and stop.
- Record **both** `{basename}` (the repo dir name) and `{name}` (the vault folder) — Step 2 needs
  both to write an honest mapping.

### Step 2 — Build the block content
Generate this exact block (paths are already resolved — `{{VAULT_PATH}}`/`{{CLAUDE_PATH}}` are real
absolute paths in the installed copy of this file):

```markdown
<!-- BRAIN:POINTERS v1 — managed by /brain. Do not edit between these markers; run `/brain pointer` to refresh. -->
## Brain OS pointers — where this project's memory lives

This repo is linked to a Brain OS vault (the journal: intent, decisions, status) and optionally a
graphify code graph (the map: structure). An agent working here loads durable context from these.

- **Vault project:** `{{VAULT_PATH}}/Projects/{name}/`
  - Status (current phase / next steps): `{name}-status.md`
  - Decisions + rationale: `{name}-decisions.md`
  - Session log (what happened each session): `{name}-session-log.md`
  - Knowledge wiki: `{name}.md` · Agenda/backlog: `{name}-agenda.md`
  - Load it all at once: `/brain start`
- **Code graph (graphify):** {GRAPH_LINE — pick one in Step 2a}
- **Name mapping (join key):** {MAPPING_LINE — pick one in Step 2b}

_Brain manages only the block between the BRAIN:POINTERS markers; everything else in this file is yours._
<!-- BRAIN:POINTERS END -->
```

**Step 2a — the graph line.** Check whether `{{CLAUDE_PATH}}/brain-graphs/{name}/graph.json` exists:
- exists → `` `{{CLAUDE_PATH}}/brain-graphs/{name}/graph.json` · query: `/brain map {name} -q "…"` · pointer note: `Projects/{name}/{name}-code-map.md` ``
- absent → ``not built yet — run `/brain map {name}` to generate``

**Step 2b — the mapping line.** Compare `{basename}` to `{name}`:
- equal → `` repo dir `{basename}` ↔ vault folder `Projects/{name}` (identical — the zero-config working-dir→vault auto-map). ``
- different → `` ⚠ repo dir `{basename}` ↔ vault folder `Projects/{name}` — **basename ≠ vault name**, so this explicit mapping is the source of truth. Keep it here. ``

### Step 3 — Apply to `{repo_root}/CLAUDE.md`
Compute the new full file content, then write only if it differs (so `end` produces a zero-diff
no-op when nothing changed):

- **CLAUDE.md absent** → create it as:
  ```markdown
  # CLAUDE.md

  Guidance for Claude Code / agents working in this repo. Run `/init` to generate full codebase docs.

  {block from Step 2}
  ```
- **CLAUDE.md present, markers present** → replace the span from the line containing
  `BRAIN:POINTERS` (the START marker) through the line containing `BRAIN:POINTERS END`
  (inclusive) with the freshly generated block. Leave every other byte untouched.
- **CLAUDE.md present, markers absent** → append a blank line + the block at end of file.

Write UTF-8 **without BOM**. If the computed content equals the current file, write nothing.

`--dry-run`: print the block and state which case applies (create / update-in-place / append /
no-op). Write nothing.

### Step 4 — Report
```
Pointer block {created|updated|unchanged} in {repo_root}/CLAUDE.md
  Vault:  {{VAULT_PATH}}/Projects/{name}/
  Graph:  {built: …/brain-graphs/{name}/graph.json | not built}
  Map:    repo `{basename}` ↔ vault `{name}`{ ⚠ differ}
```

## Design notes
- **One block, nothing else.** This is the single deliberate exception to Brain OS's "don't touch
  the repo" rule. The sentinel markers contain the blast radius to one region; hand-written docs
  are never modified. `new-project` and `end` call this logic; `rename` only *emits* the command
  (the repo dir may be mid-rename, so brain can't locate `CLAUDE.md` reliably then).
- **Write-if-changed** is what makes wiring this into `end` safe — an unchanged block means a
  byte-identical file means no git noise.
- **The mapping line is the point.** The repo-dir↔vault-folder name coupling is usually identical
  (zero-config), but when it isn't, an agent guessing the basename would read the wrong (or no)
  vault folder. Writing the resolved mapping explicitly is what keeps agents aligned.
