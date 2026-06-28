## sync {project}

Synchronise the global agent registry AND validate vault graph integrity. Run after any agent-register, status change, or when the Obsidian graph looks sparse.

**Arguments**: `{project}` — project name (omit to run graph integrity check only)

---

## Step 1 — Agent registry sync (skip if no project arg)

1. Read `{{VAULT_PATH}}/Projects/{project}/_brain/registry/agents.md` — get all agents for this project.
2. Read `{{VAULT_PATH}}/Claude/agents.md` — get current global registry (create if missing).
3. For each project agent:
   - If agent_id exists in global registry: update row (status, model, last_seen)
   - If not: append new row
4. Write updated `{{VAULT_PATH}}/Claude/agents.md`.

**Claude/agents.md format**:
```markdown
# Global Agent Registry
> Updated by /brain sync. Do not edit manually.

| agent_id | project | role | status | model | last_synced |
|----------|---------|------|--------|-------|-------------|
| sc-research-001 | social-content | research | active | claude-sonnet-4-6 | 2026-04-27 |
```

---

## Step 2 — Graph integrity check (always runs)

Brain OS writes files but never validates what it wrote. This step catches broken wikilinks before they silently degrade the graph.

**2a. Build the file index**

Collect all `.md` files in the vault (excluding `.obsidian/`, `_deprecated/`, `_raw/`). Record each filename (without extension) and its full relative path.

**2b. Scan for wikilinks**

For each file in scope, extract all `[[wikilink]]` and `[[path/to/file|alias]]` patterns. For each link:
- Strip alias (`|alias` part) and `.md` extension if present
- Resolve: check if the target filename exists anywhere in the file index
- Mark as **broken** if no match found

**2c. Check projects-index consistency**

- Every project listed in `{{VAULT_PATH}}/Claude/projects-index.md` must have a matching `Projects/{name}/{name}.md` file
- Every project folder in `Projects/` must have an entry in projects-index (orphan folder detection)

**2c-bis. Check canonical file completeness (per project)**

Every project folder must contain the PREFIXED canonical set. Flag any that are missing:
- `{name}.md` (wiki root — NOT `index.md`)
- `{name}-status.md`
- `{name}-session-log.md`
- `{name}-decisions.md`
- `{name}-agenda.md`
- `captures/captures.md` (warn-only — captures are optional)

Also flag any UNPREFIXED `status.md` / `index.md` / `session-log.md` / `decisions.md` found in a
project folder — these are drift artifacts from the old naming and should be renamed to the
prefixed form. `--fix` creates any missing file from the `new-project` templates (empty, with
the correct `> See also:` wikilink header) and reports renames for manual confirmation (never
auto-overwrite existing content).

**2c-ter. Auto-index loose notes (the no-orphans projector — this is the scaling safety net)**

The filesystem is the source of truth; the AI may drop a freeform note straight into a project
folder without going through `capture`/`new-project`, so it gets no `[[link]]` and floats as an
orphan in the graph. `sync` fixes this deterministically — connectivity is *derived from the
folder*, never from the AI remembering to link. For each project:
- A **loose note** = a top-level `.md` in `Projects/{name}/` that is NOT in the canonical set
  (`{name}.md`, `{name}-status/-session-log/-decisions/-agenda/-code-map.md`) and is not already
  linked from `{name}.md`.
- **Living doc** (no date in the filename, no `status: archived` frontmatter) → with `--fix`,
  append `- [[note]]` under a `## Documents` section in `{name}.md` (create the section if
  absent). Purely additive — never touch existing prose.
- **Dated snapshot** (filename matches `\d{4}-\d{2}-\d{2}`, or `status: archived`) → do NOT
  index (don't resurrect dead notes into the active graph). Report it as an **archive
  candidate**; `--fix --archive` moves it to `Projects/{name}/_archive/` (which `sync` skips).
- This is **idempotent**: once a note is listed in `## Documents`, it is "linked" and is skipped
  on the next run. Re-running `sync --fix` on a clean vault is a no-op.

This is what makes the brain scale without AI discipline: write freely, then `sync` projects the
structure. Verified on the live vault: 12 living docs indexed, 6 snapshots flagged, re-run a no-op.

**2c-quater. Pointer-block presence (read-only — never writes)**

Only when a `{project}` arg is given AND the working directory is obviously that project's repo
root (its basename resolves to `Projects/{project}/`, or the user confirms the repo path): check
that `{repo}/CLAUDE.local.md` contains a `BRAIN:POINTERS` block AND that `CLAUDE.local.md` is
gitignored (`git check-ignore` echoes it). If the block is missing, or the file exists but isn't
ignored, advise `run /brain pointer {project}` (it fixes both). **sync never writes the repo** — not
even with `--fix`; repo writes are exclusively `/brain pointer`'s job. If the repo root can't be
resolved (sync is vault-wide and brain-os can't assume a repo location), **skip this check
silently** — do not guess a path.

**2d. Report**

```
Graph integrity check — {YYYY-MM-DD}

  Files scanned: {N}
  Wikilinks checked: {M}

  ✅ OK — no broken links
```

Or if issues found:
```
Graph integrity check — {YYYY-MM-DD}

  Files scanned: {N}
  Wikilinks checked: {M}

  ⚠️  Broken links ({K} found):
    Claude/projects-index.md → [[old-status]] — no file named 'old-status' exists
    Projects/brain-os/brain-os.md → [[brain-os-decisions]] — file missing

  ⚠️  Orphan project folders ({J} found):
    Projects/claude-skills/ — no entry in projects-index.md

  Run `/brain sync --fix` to auto-remove broken links and add orphan folder entries.
```

**2e. Auto-fix (if `--fix` flag passed)**

For each broken link:
- If the link is in a "See also" line: remove just that `[[link]]` token from the line
- If the link is the only content on a line: remove the whole line
- Do not auto-fix links inside body content — flag those for manual review

For each orphan project folder:
- Add a row to `Claude/projects-index.md` with status "unregistered" and today's date
- User can then update phase/status manually

---

## Step 3 — Report summary

```
/brain sync complete — {YYYY-MM-DD}

  Agent registry: {N} agents synced, {M} new
  Graph integrity: {K} broken links, {J} orphan folders
  Action: {none required | run /brain sync --fix to repair}
```
