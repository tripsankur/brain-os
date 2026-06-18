## map

Build or query a project's **code knowledge graph** using [graphify](https://graphifylabs.ai/)
(`graphifyy` on PyPI). graphify is now the code-map engine for Brain OS — it replaces the
old heuristic, first-40-lines `code-map.md` index with a real AST + semantic graph
(functions/classes/concepts as nodes, calls/imports/references as edges, community
detection, god-node ranking, and a persistent queryable `graph.json`).

Brain owns the *journal* (intent, decisions, status, agenda). graphify owns the *map*
(structure). This subcommand is the bridge: it builds the map and writes a thin vault
pointer so future sessions know the code is mapped and how to query it.

## Usage

```
/brain map [project-name]            # build/refresh the graph on the project repo
/brain map [project-name] --refresh  # force a full rebuild (else incremental)
/brain map [project-name] -q "..."   # query the existing graph (no rebuild)
```

- `project-name` — defaults to the project inferred from the current working directory.
- Output graph: `{repo-root}/graphify-out/graph.json` (+ `graph.html`, `GRAPH_REPORT.md`).
- Output vault pointer: `{{VAULT_PATH}}/Projects/{name}/{name}-code-map.md`.

---

## Execution

### Step 1 — Resolve project and repo root

- If `project-name` given: confirm `Projects/{name}/` exists in the vault. Derive the repo
  root (ask the user to confirm the repo path if it is not obvious from the working directory).
- If no arg: derive the project name from the working directory.
- If `Projects/{name}/` is missing, halt: "No vault project for '{name}'. Run `/brain new-project {name}` first."

### Step 2 — Ensure graphify is installed

graphify is a hard dependency of `/brain map`. Detect an interpreter that can `import graphify`
(prefer `uv tool`, then `pipx`, then the active `python`). If none is found, install it:
`pip install graphifyy` (or `uv tool install graphifyy`). Save the resolved interpreter path to
`graphify-out/.graphify_python` so later steps reuse it.

> Windows note: graphify's extraction uses a process pool — any driver `.py` you write must be
> guarded by `if __name__ == "__main__": multiprocessing.freeze_support()`.

### Step 3 — Query path (`-q` given, graph already exists)

If `graphify-out/graph.json` exists and the user passed `-q "<question>"` (or asked a
natural-language question about the codebase), do NOT rebuild — answer from the graph:

```
graphify query "<question>"
```

Quote `source_location` when citing a specific fact. Fall back to an inline NetworkX
traversal of `graph.json` only if the `graphify query` CLI is unavailable.

### Step 4 — Build path (default, or `--refresh`)

Run the graphify pipeline on the repo (this is exactly what the `/graphify` skill does — you
may invoke that skill instead of re-implementing it):

- `--refresh` → full rebuild. Otherwise prefer incremental: `graphify . --update`.
- Scope to source; graphify already skips `node_modules/`, `.venv/`, `dist/`, `__pycache__/`.
- Structural (AST) extraction is free and deterministic. Semantic extraction of docs/images
  runs via subagents (no API key needed — the host session is the LLM); skip low-value
  binaries/screenshots unless the user asks.

### Step 5 — Write the vault pointer `{name}-code-map.md`

graphify's graph lives in the repo and is gitignored, so the journal needs a durable pointer
that survives without the repo checked out. Write
`{{VAULT_PATH}}/Projects/{name}/{name}-code-map.md`:

```markdown
# Code Map — {name}
> See also: [[{name}]] | [[{name}-status]]
> Backend: graphify | Graph: {repo-root}/graphify-out/graph.json
> Generated: {YYYY-MM-DD} | Commit: {hash} | {N} nodes · {E} edges · {C} communities

## How to query
Run `/brain map {name} -q "<question>"` (or `graphify query "<question>"`) — answers from the
graph instead of scanning source.

## God Nodes (core abstractions)
| Node | Edges | File |
|------|-------|------|
| `{node}` | {n} | `{path}` |

## Communities (subsystems)
- {community label} — {one-line description}

## Notes
- Rebuild after structural changes: `/brain map {name} --refresh`.
- Auto-rebuild on commit: install the graphify post-commit hook (`graphify hook install`).
```

Pull the god-nodes, community labels, and counts from `GRAPH_REPORT.md` / `graph.json`.

### Step 6 — Report

```
Code map (graphify) for {name}: {N} nodes · {E} edges · {C} communities
  God nodes: {top 3}
  Graph:   {repo-root}/graphify-out/graph.json  (graph.html to browse)
  Pointer: Projects/{name}/{name}-code-map.md

Query it any time: /brain map {name} -q "how does X work?"
```

---

## Design notes

- **graphify is the single code-map engine.** The previous Explore-agent heuristic index is
  retired; do not regenerate the old `code-map.md` format.
- The graph is a snapshot. Rebuild when module structure changes — not every session. The
  post-commit hook keeps it fresh automatically when installed.
- The vault pointer (`{name}-code-map.md`) is the journal's durable handle on the map; the
  full graph is regenerable and gitignored, so never commit `graphify-out/`.
- Brain↔graphify routing: code-structure questions → this subcommand / graphify; intent,
  decisions, status, agenda → the rest of `/brain`.
