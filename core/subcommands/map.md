## map

Build or query a project's **unified knowledge graph** with [graphify](https://graphifylabs.ai/)
(`graphifyy` on PyPI) — one graph over **both the code repo and the vault notes**, so code symbols
and the intent behind them (decisions, concepts, status) live in a single queryable structure.

This is the Map layer of Brain OS: Brain owns the *journal* (intent), graphify owns the *map*
(structure), and `/brain map` joins them. Verified: a query for a domain concept (e.g. "IDM" /
"Strong Low") traverses from the doc-derived concept node **into the implementing code**
(`detect_structure`, `StructureState`) — code↔intent cross-edges genuinely form.

> **Optional dependency.** graphify is required *only* for `/brain map`. The rest of Brain OS
> (`start`, `end`, `status`, `recall`, `agenda`, `sync`, …) works with zero extra dependencies.
> Don't install graphify unless you want the code/associative graph.

## Usage

```
/brain map [project]            # build/refresh the unified graph (code repo + vault notes)
/brain map [project] --refresh  # full rebuild (else incremental --update)
/brain map [project] -q "..."   # query the existing graph (no rebuild)
/brain map [project] --code-only # graph the repo only (skip vault notes)
/brain map [project] --vault-only# graph the vault notes only (for non-code projects)
```

- `project` defaults to the project inferred from the working directory.
- **Graph cache (central, uniform):** `{{CLAUDE_PATH}}/brain-graphs/{name}/graph.json` (+ `graph.html`,
  `GRAPH_REPORT.md`). Central — NOT in the repo tree and NOT in the vault — so it works the same
  for code+notes and notes-only projects, and never dirties either store. It is a regenerable
  cache; safe to delete.
- **Vault pointer:** `{{VAULT_PATH}}/Projects/{name}/{name}-code-map.md` (god-nodes + how to query).

## Sources (the two paths)

`/brain map` builds one graphify graph over the union of:
1. **Code repo** — resolved from the project (working-dir basename ↔ `Projects/{name}`, the same
   join key `/brain rename` keeps aligned). Skipped if no repo exists (vault-only project).
2. **Vault notes** — `{{VAULT_PATH}}/Projects/{name}/` (status, decisions, session-log, wiki,
   captures). Skipped with `--code-only`.

**Single-corpus staging (architecture-critical).** Code↔intent cross-edges only form when code and
notes are extracted in ONE pass — the semantic extractor must see both to link a concept to its
implementing symbol. (Proven: a concept node like `IDM`/`Strong Low` reaches `detect_structure`/
`StructureState` only because CLAUDE.md was extracted *alongside* the code.) graphify's native
multi-path mode builds each source separately then merges, which can leave two disconnected islands
joined only by coincidental id matches. So `/brain map` does NOT merge-after — it **stages both
sources under one temporary scan root and runs a single graphify pass**, then cleans up the staging
dir. Co-locating the notes in the repo is therefore unnecessary — staging does the joining at build
time without moving anything.

## Execution

### Step 1 — Resolve project + sources
- Derive `{name}`; confirm `Projects/{name}/` exists (else: "run /brain new-project first").
- Resolve repo root (confirm with the user if not obvious from the working dir). If none, this is a
  vault-only build (`--vault-only` implied).
- Build the source list: `[repo_root?]` + `[{{VAULT_PATH}}/Projects/{name}]` per the flags.

### Step 2 — Ensure graphify
Detect an interpreter that can `import graphify` (uv → pipx → active `python`); install
`graphifyy` if absent. Save it to `{{CLAUDE_PATH}}/brain-graphs/{name}/.graphify_python`.
> Windows: any driver `.py` must guard `if __name__ == "__main__": multiprocessing.freeze_support()`
> (graphify extraction uses a process pool).

### Step 3 — Query path (`-q`, graph exists)
If `graph.json` exists and the user asked a question, do NOT rebuild — `graphify query "<q>"`
against the cached graph. Cross-queries are the point: ask "which code implements {concept}?" or
"what decision led to {module}?" and let the traversal cross the doc↔code boundary. Quote
`source_location` when citing.

### Step 4 — Build path (default / `--refresh`)
1. **Stage one corpus.** Create a temp scan root (e.g. `{{CLAUDE_PATH}}/brain-graphs/{name}/_stage/`).
   Junction/symlink (or copy) the repo as `code/` and the vault project as `notes/` under it, so a
   single extraction pass sees both. Exclude `node_modules/`, `.venv/`, `dist/`, `_archive/`,
   `graphify-out/`, `.git/`.
2. **One graphify pass** over the staging root (invoke the `/graphify` skill — don't re-implement),
   writing outputs to `{{CLAUDE_PATH}}/brain-graphs/{name}/`. AST over code is free/deterministic;
   semantic extraction over docs+notes runs via subagents (no API key — the host session is the LLM).
   `--refresh` → full rebuild; else incremental `--update`.
3. **Tear down** the staging junctions/symlinks (keep only the graph outputs). If junctions aren't
   available, fall back to `--code-only`/`--vault-only` single-source builds and warn that
   cross-edges won't span the two stores.
- Scope note: the vault project folder is small; the repo dominates node count.

### Step 5 — Write the vault pointer `{name}-code-map.md`
Per the template in the previous spec — header carries the cache path, commit, and node/edge/
community counts; sections list God Nodes and Subsystems; "How to query" points back here. The
graph is a regenerable cache, so this pointer is the journal's durable handle on it.

Then run the `pointer` subcommand logic for `{name}` (write-if-changed) so the repo `CLAUDE.md`
graph line flips from "not built" to the cache path + query command immediately, instead of waiting
for the next `/brain end`. Skip on `--vault-only` / no repo.

### Step 6 — Report
```
Unified map for {name}: {N} nodes · {E} edges · {C} communities  ({code} code + {notes} notes sources)
  God nodes: {top 3}
  Cache:   {{CLAUDE_PATH}}/brain-graphs/{name}/graph.json  (graph.html to browse)
  Pointer: Projects/{name}/{name}-code-map.md
Cross-query it: /brain map {name} -q "which code implements <concept>?"
```

## Design notes
- **Two stores, one graph.** Code stays in the repo, the journal stays in the vault; graphify
  merges both into the cache. Co-location is unnecessary and would cost the cross-project vault +
  clean repos.
- **Central cache** keeps code+notes and notes-only projects uniform and both stores clean. Never
  commit it; it regenerates.
- The graph is a snapshot — rebuild when structure changes, not every session. The graphify
  post-commit hook keeps the *code* side fresh automatically.
- graphify is optional and scoped to this one command — Brain OS itself has no hard dependency on it.
