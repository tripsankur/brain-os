# `/brain map` — Code Map Subcommand Spec

## Problem

At 100+ files, Claude cannot scan an entire codebase before doing useful work. Context fills with orientation, leaving no room for the actual task. The vault stores decisions and status — not code structure. Every session starts blind.

## Solution

A `code-map.md` per project, stored in the vault. Not a code mirror — a navigation index. Claude reads it at session start to orient in seconds, then reads only the specific files the task requires.

---

## Command Signature

```
/brain map [project-name] [--refresh]
```

- `project-name` — optional; defaults to the project inferred from the working directory
- `--refresh` — force regeneration even if an up-to-date map exists
- Output: `{vault}/Projects/{name}/code-map.md`

---

## Algorithm

Claude executes the scan inline (Type 1 subcommand — no Agent() spawns):

1. **Resolve project root** — from working directory or explicit `project-name` arg
2. **Check staleness** — if `code-map.md` exists and git HEAD matches stored commit hash, report "Map is current" and exit unless `--refresh`
3. **Glob the repo** — collect all files, apply scope rules (see below)
4. **Group by module** — use directory structure to infer module boundaries; flag entry points (files named `index.*`, `main.*`, `{project-name}.*`, or root-level orchestrators)
5. **Summarise each file** — read each file, extract: one-line purpose, key exports/interfaces/functions (top 3–5), any explicit `@module` or doc comment
6. **Write `code-map.md`** — structured output (schema below)
7. **Update vault session log** — append one line: `[date] | brain map | {project} — {N} files mapped`

### Heuristics for file purpose

Claude infers purpose from:
- Filename and directory path
- First 30 lines of the file (imports, exports, top-level declarations)
- Explicit doc comments or frontmatter
- For markdown skill files: the `##` heading structure

No AST parsing — this is approximate by design. Navigation index, not exhaustive documentation.

---

## Output Schema: `code-map.md`

```markdown
# Code Map — {project-name}
> Generated: YYYY-MM-DD | Commit: {git-hash-short} | Files: {N}
> Stale if commit differs. Run `/brain map {project} --refresh` to regenerate.

## Entry Points
- `{path}` — {purpose}

## Module: {directory-name}
| File | Purpose | Key exports |
|------|---------|-------------|
| `{rel-path}` | {one-line purpose} | `Export1`, `Export2` |

## Module: {directory-name}
...

## Skipped
- `{path-pattern}` — {reason} (e.g. `node_modules/` — dependency tree)
```

Rules:
- Entry points section comes first — these are the files Claude most often needs
- Each module maps to one directory; nested dirs get their own module section
- Key exports: max 5 per file; omit for config/data files
- Skipped section documents what was excluded and why

---

## Staleness Model

The map header stores the short git commit hash at generation time. At session start, Claude checks:

```
stored hash == git rev-parse --short HEAD
```

- **Match** → map is current, read and trust it
- **Mismatch** → map may be stale; surface a warning:
  > "Code map last generated at `{hash}`. Current HEAD is `{current}`. Run `/brain map --refresh` if architecture has changed."
- **No git** → use file modification timestamps; warn if any source file is newer than the map

Regeneration is not automatic by default. The map is a **snapshot of stable architecture**, not a live mirror. Regenerate when:
- Module structure changes (new directories, new entry points)
- Major refactor completes
- New project, first time

---

## Session Start Integration

Add to the session start rule in `CLAUDE.md` (per project):

> If `Projects/{name}/code-map.md` exists, read it before reading source files. Use it to identify which files are relevant to the current task before opening them. If the map is stale, note it but proceed.

This keeps orientation out of the working context — Claude reads the index, not the codebase.

---

## Scope Rules

### Include
- Source files: `*.ts`, `*.tsx`, `*.js`, `*.py`, `*.go`, `*.rs`, `*.md` (skill files), `*.json` (configs/manifests)
- Root-level configs: `package.json`, `pyproject.toml`, `go.mod`, `module.json`
- Entry points regardless of extension

### Skip
- `node_modules/`, `.venv/`, `dist/`, `build/`, `__pycache__/` — dependency/build artifacts
- `*.lock`, `*.min.*` — generated files
- `_deprecated/` — archived, not active
- `tests/fixtures/` — test data, not architecture
- Binary files, images, fonts

### Configurable (future)
- Max directory depth (default: unlimited)
- Additional skip patterns via `module.json` → `map_ignore` array
- Include/exclude specific extensions

---

## Limitations

- **Approximate**: Claude infers purpose from heuristics, not static analysis. A file with a misleading name or no comments may be summarised incorrectly.
- **Snapshot, not live**: the map reflects code at generation time. Stale maps misdirect.
- **Size cap**: for very large projects (500+ files), Claude may need to map module by module to stay within context. Future: `--module {name}` flag to scope the scan.
- **No cross-file dependency graph**: the map shows what each file does, not how files call each other. A full dependency graph is a Tier C feature.

---

## Implementation Plan

1. Write `core/subcommands/map.md` — the skill file Claude reads to execute this subcommand
2. Add `map` to the dispatch table in `core/brain.md`
3. Add session start rule to `CLAUDE.md` template (or document in `docs/creating-a-module.md`)
4. Add to `tests/unit/dispatch-table.sh` — verify map entry exists
5. Manual e2e test: run `/brain map brain-os` against the live repo, verify output

---

## Future: Tier C Code Intelligence

With background workers:
- **Auto-regen on commit**: worker detects `git push` or file change, regenerates map
- **Dependency graph**: static analysis pass builds `imports-map.md` (who calls what)
- **Drift detection**: worker flags when map hasn't been regenerated after N commits
- **Semantic search**: embed map entries, support "find files related to auth" queries
