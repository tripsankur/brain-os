## agenda

Read, add to, or advance a project's **agenda** — the prioritized task backlog the brain holds
for a project. The agenda is the bridge between the journal (Brain) and the hands (loops /
Tier-C background workers): a `/loop` or scheduled worker pulls the top `todo` item, executes
it, and reports back. "Brain assigns tasks for loops on a given agenda" = this file driving that
loop.

File: `{{VAULT_PATH}}/Projects/{name}/{name}-agenda.md` (scaffolded by `/brain new-project`).

## Usage

```
/brain agenda [project]               # show the agenda (Active + top todos)
/brain agenda [project] add "<task>" [--pri P1|P2|P3] [--accept "<criteria>"]
/brain agenda [project] next          # print the single highest-priority `todo` (what a loop runs next)
/brain agenda [project] start <id>    # mark an item `doing`
/brain agenda [project] done <id>     # mark an item `done`, move it to the Done section
/brain agenda [project] block <id> "<reason>"   # mark `blocked` with a reason
```

`project` defaults to the project inferred from the working directory.

## Schema

`{name}-agenda.md`:

```markdown
# {Name} — Agenda
> See also: [[{name}]] | [[{name}-status]] | [[{name}-session-log]]
> Prioritized backlog. `/brain agenda next` returns what `/loop` runs next. Move finished items to Done.

## Active
| ID | Pri | Task | Status | Acceptance |
|----|-----|------|--------|------------|
| A3 | P1  | Fix X | todo    | tests pass |
| A2 | P2  | Doc Y | doing   | README updated |
| A1 | P2  | Z     | blocked | (waiting on user creds) |

## Done
- [x] A0 — Initial task (2026-06-18)
```

Rules:
- **ID**: `A{n}`, monotonically increasing, never reused.
- **Pri**: `P1` (do first) > `P2` > `P3`. Ties broken by lowest ID (oldest first).
- **Status**: `todo` → `doing` → `done`, or `blocked`. Only `todo` items are eligible for `next`.
- **Acceptance**: a one-line, checkable definition of done — this is what a loop verifies before marking `done`.

## Execution

### show
Read the agenda; print the `## Active` table plus a one-line "Next:" pointing at the top `todo`
(highest Pri, lowest ID). If the file is missing, offer to create it (it is scaffolded by
`new-project`; create an empty one if the project predates this feature).

### add
Append a row to `## Active` with the next free `A{n}` id, given Pri (default `P2`), `todo`
status, and acceptance criteria (default "(define)"). Report the new id.

### next
Select the eligible item: status `todo`, highest Pri, then lowest ID. Print just that row.
This is the contract a loop calls each iteration. If no `todo` exists, print `AGENDA EMPTY`.

### start / done / block
Update the named item's status in place. On `done`, move the row out of `## Active` into
`## Done` as `- [x] {id} — {task} ({today})`. On `block`, append the reason in the Acceptance
cell. Keep the table sorted by Pri then ID.

---

## Driving a loop from the agenda

The loop contract (see `docs/loops-and-agenda.md`): each iteration —
1. `/brain agenda {name} next` → get the top todo (or stop on `AGENDA EMPTY`).
2. `/brain agenda {name} start <id>`.
3. Execute the task. Verify against its Acceptance line.
4. `/brain agenda {name} done <id>` (or `block <id>` with a reason).
5. Append a `## [date] | {id}: {summary}` line to `{name}-session-log.md`.

A human-paced run uses `/loop` with no interval (model self-paces through the agenda). A
Tier-C background worker runs the same contract on a cron schedule (`async: true` hook).
Either way the agenda is the single source of truth for "what to do next" — the brain assigns,
the loop executes, the journal records.
