# Claude Session Workflow
> See also: [[preferences]] | [[projects-index]] | [[log]]
> Canonical protocol for how Brain OS reads and writes this vault. Generic — safe to ship.

## Layers (Journal · Map · Hands)
- **Journal** = this vault. Intent, decisions, status, session log, preferences, agenda.
- **Map** = graphify (optional). `/brain map` builds a code+notes graph for associative recall.
- **Hands** = agenda + loops. `{name}-agenda.md` is the backlog `/brain agenda next` / `/loop` consume.

## Session Start Protocol
1. Read `Claude/preferences.md` and `Claude/projects-index.md` (often auto-injected by the hook).
2. If working on a project, read `Projects/{name}/{name}-status.md` and its `{name}-agenda.md`.
3. Process any files in `_raw/inbox/` per the routing rules below.

## Session End Protocol (`/brain end`)
1. Append a one-line entry to `Projects/{name}/{name}-session-log.md`: `## [YYYY-MM-DD] | summary`.
2. Update the `## Current` section of `Projects/{name}/{name}-status.md` (preserve `## History`).
3. Reconcile `Projects/{name}/{name}-agenda.md` (done items → Done; new tasks → todo).
4. Append decisions to `Projects/{name}/{name}-decisions.md`; append one line to `Claude/log.md`.
5. Run `/brain sync --fix {name}` — projects loose notes into `{name}.md`, repairs links.

## Canonical file set (prefixed folder-note pattern)
`Projects/{name}/`: `{name}.md` (wiki) · `{name}-status.md` · `{name}-session-log.md` ·
`{name}-decisions.md` · `{name}-agenda.md` · `{name}-code-map.md` (if mapped) · `captures/` ·
`_archive/` (dated snapshots, excluded from the active graph). Never write unprefixed
`status.md`/`index.md` — the read/recall paths expect the prefixed names.

## Inbox Routing Rules (`_raw/inbox/`)
- Architectural insight / domain knowledge → `Projects/{name}/{name}.md`
- Decision → `Projects/{name}/{name}-decisions.md`
- Task / next step → `Projects/{name}/{name}-status.md` (Next Steps) or `{name}-agenda.md`
- Session note → `Projects/{name}/{name}-session-log.md`
- After routing, move the file to `_raw/processed/YYYY-MM-DD-{filename}`.

## Tiered Retrieval (keep context cheap, scales)
1. Read `{name}-status.md` / `{name}.md` first.
2. Drill into full wiki pages only when the index pointer is insufficient.
3. Never load entire project trees speculatively — use `/brain map -q` for associative questions.

## Personal/ Access Control
Do NOT read `Personal/` unless the user explicitly grants access this session.
