# Brain OS — Journal, Map, Hands

How the three layers of Brain OS fit together, and how an agenda in the brain drives loops.

## The three layers

Brain OS is one memory+automation OS over two stores and an execution layer. Each owns a
distinct question; nothing is duplicated across them.

| Layer | Engine | Owns | Question it answers | Lifecycle |
|-------|--------|------|---------------------|-----------|
| **Journal** | Brain (Obsidian vault) | intent, decisions, status, session log, preferences, **agenda** | *why / when / what's next / what did we do* | written during work, append-mostly, spans projects |
| **Map** | **graphify** (code graph) | code structure: functions/classes/concepts + calls/imports/refs | *what-is / how-connected / where's X / what calls Y* | regenerated from source, per-repo, snapshot |
| **Hands** | **loops / Tier-C workers** | task execution against the agenda | *do the next thing* | pulls a task, executes, reports back |

Routing rule (also in the global `~/.claude/CLAUDE.md`): code-structure questions → Map
(graphify / `/brain map`); intent/decision/status/agenda → Journal (`/brain …`). Never copy
code facts into the journal (they rot); never store decisions in the graph (it's overwritten on
rebuild). **Map = redraws itself. Journal = remembers why.**

## Map: graphify replaces the heuristic `/brain map`

`/brain map` is now a thin driver over [graphify](https://graphifylabs.ai/) (`graphifyy` on
PyPI). The old first-40-lines Explore heuristic is retired. graphify gives a real AST + semantic
graph (nodes = symbols/concepts, edges = calls/imports/references), community detection,
god-node ranking, and a persistent queryable `graph.json`.

- `/brain map {name}` builds/refreshes the graph on the repo; writes a durable vault pointer
  `Projects/{name}/{name}-code-map.md` (god-nodes + how to query) so the journal still "knows
  the code" even without the repo checked out (the graph itself is in-repo and gitignored).
- `/brain map {name} -q "<question>"` answers from the graph (no rebuild).
- Freshness: `graphify hook install` rebuilds on every commit.

> Product note: in the *publishable* brain-os, graphify is the documented code-map backend and a
> hard dependency of `/brain map`. (Decision recorded in `decisions.md`.)

## Journal: the agenda is a first-class file

Every project now has the prefixed canonical set:
`{name}.md` · `{name}-status.md` · `{name}-session-log.md` · `{name}-decisions.md` ·
**`{name}-agenda.md`** · `{name}-code-map.md` (graphify pointer) · `captures/`.

`{name}-agenda.md` is a prioritized backlog with state (`todo → doing → done`/`blocked`),
priority (`P1>P2>P3`), and a one-line **acceptance** criterion per task. See the `agenda`
subcommand for the schema and the editing verbs (`show / add / next / start / done / block`).

## Hands: how the brain assigns tasks to a loop

The agenda is the contract between the journal and a loop. One loop iteration:

1. `/brain agenda {name} next` → the single highest-priority `todo` (or `AGENDA EMPTY` → stop).
2. `/brain agenda {name} start <id>` → mark `doing`.
3. Execute the task. Verify the result against its **Acceptance** line.
4. `/brain agenda {name} done <id>` (or `block <id> "<reason>"`).
5. Append `## [date] | {id}: {summary}` to `{name}-session-log.md`.

Two execution modes, same contract:

- **Self-paced loop (available now):** `/loop` with no interval — the model works through the
  agenda top-down in-session, stopping at `AGENDA EMPTY` or a `blocked` wall. Good for "clear the
  backlog while I'm away." This is the **minimal working slice** shipped first.
- **Tier-C background worker (designed, not built):** the same contract on a cron schedule
  (`async: true` hook) — e.g. a nightly worker that drains low-risk `P3` agenda items and reports
  in the session log. This is the existing architecture's **Type 3 background worker**, now given
  a concrete job description (the agenda) rather than ad-hoc candidate tasks.

### Mapping to the existing taxonomy

| This doc | Existing architecture |
|----------|----------------------|
| Self-paced agenda loop | Type 1 subcommand flow (`/brain agenda` + `/loop`), in-session |
| Tier-C agenda worker | Type 3 background worker (Tier C), `async: true` hook |
| Agenda file | New canonical journal artifact, consumed by both |

### Guardrails for autonomous loops

- A loop only ever runs `todo` items whose **acceptance is checkable**; if acceptance is
  `(define)`, it surfaces the item for the human instead of guessing.
- Anything outward-facing or irreversible (push, deploy, install, send) is marked `blocked` with
  reason `needs-human` and never auto-run — consistent with how the classifier gated the pip /
  hook / install steps during this very build.
- Every iteration writes to the session log, so an autonomous run is fully auditable after.

## Status

- Journal schema + agenda: **shipped** (canonical specs fixed, all projects normalized).
- Map (graphify) replacing `/brain map`: **shipped** (subcommand rewritten; graphify installed).
- Self-paced agenda loop: **slice shipped** (one project seeded, contract proven).
- Tier-C agenda worker: **designed** (this doc) — build under Tier C.
