## rename {old} {new}

Rename a project everywhere it is referenced. Because the canonical layout is the
**folder-note prefixed pattern** (`Projects/{name}/{name}.md`, `{name}-status.md`, …) and the
working-directory→vault auto-mapping keys on the project name, a rename is a cross-cutting
operation: the vault folder, every prefixed file, every `[[wikilink]]`, the projects-index, and
(ideally) the code repo directory all have to move together. This subcommand does the vault side
atomically and tells you the one manual step on the code side.

## Usage

```
/brain rename {old} {new}            # rename project {old} -> {new} (vault); preview then apply
/brain rename {old} {new} --dry-run  # show every change without writing
```

`{old}` and `{new}` are project folder names (e.g. `Order-Flow` → `order-flow`). `{new}` must be
a clean slug (letters, digits, `-`/`_`); match the case you want as the new canonical prefix.

## Why this is needed (the coupling)

| What references the project name | Breaks on a naive folder rename |
|----------------------------------|---------------------------------|
| `Projects/{name}/` folder | path changes |
| `{name}.md`, `{name}-status.md`, `{name}-session-log.md`, `{name}-decisions.md`, `{name}-agenda.md`, `{name}-code-map.md` | every filename embeds the old name |
| `[[{name}-status]]` wikilinks (in those files **and** in any other project that links across) | dangle |
| `Claude/projects-index.md` row + its `[[Projects/{name}/{name}]]` link | stale |
| `Claude/agents.md`, `Claude/modules.md`, `_brain/registry/` (if the project has agents) | stale `project` column |
| `_raw/inbox/{name}/` | orphaned inbox |
| **Code:** repo dir `…/{name}/`, its `CLAUDE.md` self-references, and the `{name}-code-map.md` graphify pointer's repo path | working-dir→vault auto-map keys on the dir basename |

## Execution

### Step 1 — Validate
- Confirm `{{VAULT_PATH}}/Projects/{old}/` exists and `{{VAULT_PATH}}/Projects/{new}/` does NOT.
- Halt if `{new}` collides with an existing folder or isn't a clean slug.

### Step 2 — Preview (always; this IS the dry-run output)
Enumerate and print, without writing:
1. Folder: `Projects/{old}/` → `Projects/{new}/`
2. Files to rename: every `{old}*.md` (prefixed set + any extra `{old}-*.md`) → `{new}*.md`. Include the bare `{old}.md` → `{new}.md`.
3. Wikilink rewrites: grep the WHOLE vault for `[[{old}` and `[[Projects/{old}/` — list every file + line. (Cross-project links count — do not scope to the folder.)
4. `Claude/projects-index.md` row (link + label).
5. `Claude/agents.md` / `Claude/modules.md` / `_brain/registry/*` rows where `project == {old}`.
6. `_raw/inbox/{old}/` → `_raw/inbox/{new}/`.
Stop here if `--dry-run`.

### Step 3 — Apply (vault)
In this order:
1. **Rename files first, then the folder.** For each `{old}*.md`, rename to the `{new}`-prefixed name. (On a case-only rename — e.g. `Order-Flow`→`order-flow` — go through a temp name, because Windows/macOS filesystems are case-insensitive: `{old}.md` → `__tmp__{new}.md` → `{new}.md`.)
2. Rename the folder `Projects/{old}/` → `Projects/{new}/` (also via temp on a case-only change).
3. Rewrite wikilinks across the whole vault: replace `[[{old}` → `[[{new}` and `[[Projects/{old}/` → `[[Projects/{new}/`. Preserve any `|alias`. Write files back as UTF-8 **without BOM**.
4. Update `Claude/projects-index.md`: the row label and its `[[Projects/{new}/{new}]]` link.
5. Update `Claude/agents.md`, `Claude/modules.md`, and `_brain/registry/*` `project` columns `{old}`→`{new}` (only if the project had agents/modules).
6. Rename `_raw/inbox/{old}/` → `_raw/inbox/{new}/`.
7. Append to `Claude/log.md`: `## [{today}] | {new} | Renamed from {old} via /brain rename`.

### Step 4 — Code side (report; mostly manual)
Print these steps for the user — the brain does not touch the repo automatically:
1. Rename the repo dir: `…/tripsankur-cc/{old}/` → `…/tripsankur-cc/{new}/` so the working-dir→vault auto-map (`CLAUDE.md`: dir basename → `Projects/{basename}`) keeps resolving. If you only rename the vault, set the new dir name to match, or the auto-map points at a missing project.
2. Update the repo's own `CLAUDE.md` if it hardcodes the old name/paths.
3. Regenerate the code-map pointer: `/brain map {new} --refresh` (the old `{old}-code-map.md` was renamed but its embedded repo path + graph location are now stale).
4. Git: a dir rename is just `git mv` of the working tree from outside; the repo's history/remote name is unaffected unless you also rename the GitHub repo.

### Step 5 — Verify
Run `/brain sync {new}` — the graph-integrity + canonical-completeness check confirms no dangling `[[{old}…]]` links remain and the new prefixed set is complete. Report:
```
Renamed {old} -> {new}: {F} files, {L} wikilinks rewritten, projects-index updated.
Manual: rename repo dir to {new} + run /brain map {new} --refresh.
Verify: /brain sync {new}  (expect 0 broken links).
```

## Design notes
- Rename is the one operation the prefixed folder-note pattern makes expensive — that's the
  trade-off for graph-legible node names. This subcommand contains the blast radius in one place.
- Always run `--dry-run` first on a project with cross-links or agents.
- The code↔vault name coupling is intentional (zero-config working-dir→vault mapping); keep the
  repo dir and vault folder names identical.
