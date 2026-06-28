## pointer [project]

Write/refresh the **brain-managed pointer file** that tells any agent (or a fresh Claude session)
opening this repo *where this project's memory lives*: the vault journal (intent) and the optional
graphify code graph (map). The pointer is written to **`CLAUDE.local.md`** — Claude Code's
per-machine, gitignored memory file, auto-loaded alongside `CLAUDE.md`. Resolved absolute paths are
machine-specific, so they must **never** land in committed source; `CLAUDE.local.md` is the correct
home and `pointer` keeps it out of git.

## Usage

```
/brain pointer [project]            # write/refresh the CLAUDE.local.md pointer block (+ gitignore it)
/brain pointer [project] --dry-run  # print the block + what would change; write nothing
```

- `project` defaults to the project resolved from the working directory (see Step 1). Pass it
  explicitly when the repo dir name ≠ the vault folder name.
- Run it from **inside the repo** — repo root is resolved from the working directory.

## Why `CLAUDE.local.md`, not `CLAUDE.md`

`CLAUDE.md` is committed and often public — absolute paths there leak the local layout and are
wrong for every other clone. `CLAUDE.local.md` is the per-developer memory file Claude Code loads
automatically and that lives only on this machine (gitignored). So: machine-specific resolved
paths → `CLAUDE.local.md`; the generic "this project uses Brain OS" context already lives in
`CLAUDE.md`/README and needs no managed block. (Want cloner auto-discovery? Add **one** path-free
line to `CLAUDE.md` by hand — `pointer` does not touch `CLAUDE.md`.)

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
- Record **both** `{basename}` (the repo dir name) and `{name}` (the vault folder).

### Step 2 — Gitignore `CLAUDE.local.md` FIRST (load-bearing — prevents re-leak)
Before writing anything, make sure `CLAUDE.local.md` can never be committed:
- If `{repo_root}/.git` exists (it's a git repo):
  - Read `{repo_root}/.gitignore` (create it if absent). If it has no line that ignores
    `CLAUDE.local.md`, append a line:
    ```
    CLAUDE.local.md
    ```
  - Verify: `git -C {repo_root} check-ignore CLAUDE.local.md` must echo the filename. If it does
    not, **stop and report** — do not write the file (writing before it's ignored risks a later
    `git add -A` committing the path).
- If not a git repo: skip gitignore; just write the file in Step 3.

### Step 3 — Build the pointer block
Generate this block (paths are already resolved — `{{VAULT_PATH}}`/`{{CLAUDE_PATH}}` are real
absolute paths in the installed copy of this file):

```markdown
<!-- BRAIN:POINTERS v1 — managed by /brain pointer. Per-machine, gitignored. Run `/brain pointer` to refresh. -->
# Brain OS pointers (local — where this project's memory lives)

This repo is linked to a Brain OS vault (the journal: intent, decisions, status) and optionally a
graphify code graph (the map: structure). The absolute paths below are machine-specific, which is
why this file is gitignored instead of being committed into `CLAUDE.md`.

- **Vault project:** `{{VAULT_PATH}}/Projects/{name}/`
  - Status (current phase / next steps): `{name}-status.md`
  - Decisions + rationale: `{name}-decisions.md`
  - Session log (what happened each session): `{name}-session-log.md`
  - Knowledge wiki: `{name}.md` · Agenda/backlog: `{name}-agenda.md`
  - Load it all at once: `/brain start`
- **Code graph (graphify):** {GRAPH_LINE — pick one in Step 3a}
- **Name mapping (join key):** {MAPPING_LINE — pick one in Step 3b}

_Managed by `/brain pointer`; refreshed by `/brain new-project` and `/brain end`. Safe to delete — it rebuilds._
<!-- BRAIN:POINTERS END -->
```

**Step 3a — the graph line.** Check whether `{{CLAUDE_PATH}}/brain-graphs/{name}/graph.json` exists:
- exists → `` `{{CLAUDE_PATH}}/brain-graphs/{name}/graph.json` · query: `/brain map {name} -q "…"` · pointer note: `Projects/{name}/{name}-code-map.md` ``
- absent → ``not built yet — run `/brain map {name}` to generate``

**Step 3b — the mapping line.** Compare `{basename}` to `{name}`:
- equal → `` repo dir `{basename}` ↔ vault folder `Projects/{name}` (identical — the zero-config working-dir→vault auto-map). ``
- different → `` ⚠ repo dir `{basename}` ↔ vault folder `Projects/{name}` — **basename ≠ vault name**, so this explicit mapping is the source of truth. Keep it here. ``

### Step 4 — Apply to `{repo_root}/CLAUDE.local.md`
`CLAUDE.local.md` may also hold the user's own local notes, so own only the marker span — never
clobber the whole file:
- **absent** → create it containing just the Step 3 block.
- **present, markers present** → replace the span from the line containing `BRAIN:POINTERS` (START)
  through the line containing `BRAIN:POINTERS END` (inclusive) with the fresh block. Leave every
  other byte untouched.
- **present, markers absent** → append a blank line + the block at end of file.

Write UTF-8 **without BOM**. The rewrite is naturally idempotent (same inputs → identical span); no
git-noise concern since the file is gitignored.

`--dry-run`: print the block + which case applies (create / replace-span / append) and confirm
`CLAUDE.local.md` is/Would be gitignored. Write nothing.

### Step 5 — Report
```
Pointer written to {repo_root}/CLAUDE.local.md (gitignored ✓)
  Vault:  {{VAULT_PATH}}/Projects/{name}/
  Graph:  {built: …/brain-graphs/{name}/graph.json | not built}
  Map:    repo `{basename}` ↔ vault `{name}`{ ⚠ differ}
```
If `CLAUDE.local.md` could not be gitignored, report that as a failure instead — never leave a
resolved path writable into committed source.

## Design notes
- **Gitignored target, by design.** Resolved absolute paths are per-machine and (in a public repo)
  a leak. They belong in `CLAUDE.local.md` — the per-developer memory Claude Code auto-loads —
  exactly like `brain-os.config.json` keeps the vault path out of committed source. Verified there
  is no `@import` syntax in `CLAUDE.md`; auto-loading `CLAUDE.local.md` is the supported path.
- **Gitignore is the safety contract.** Step 2 runs before Step 3 and is verified with
  `git check-ignore`; the file is never written until it can't be committed.
- **`new-project` and `end` call this logic; `rename` only emits the command** (the repo dir may be
  mid-rename, so brain can't locate the repo reliably then). All callers run with cwd = the repo.
- **The mapping line is the point.** When the repo-dir name ≠ the vault-folder name, an agent
  guessing the basename reads the wrong (or no) vault folder. The explicit resolved mapping is what
  keeps agents aligned.
