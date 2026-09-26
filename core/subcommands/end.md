## end

Write session back to vault. Run this at the end of every meaningful session.

**Filename convention**: every project file is PREFIXED with the project name — `{name}.md` (wiki root), `{name}-status.md`, `{name}-session-log.md`, `{name}-decisions.md`, `{name}-agenda.md`. Never write unprefixed `status.md`/`index.md`; the read/recall paths expect the prefixed names and will miss anything else.

**Wikilink rule**: every file written or appended must include `[[wikilinks]]` to related files within the same project. At minimum, each project file links to its siblings: `[[{name}]]`, `[[{name}-status]]`, `[[{name}-decisions]]`, `[[{name}-session-log]]`, `[[{name}-agenda]]`. The hub files (`Claude/workflow.md`, `Claude/log.md`, `Claude/preferences.md`, `Claude/projects-index.md`) link to each other.

**Raw vs curated**: every session is already captured automatically, raw, in `Claude/journal/` and
`Projects/{name}/{name}-activity.md` (SessionEnd hook + scheduled sweep). `end` is the curation step:
it turns raw activity into status, decisions and a readable log. It never edits the journal or activity files.

1. Ask user: "Summarize what we did this session in one sentence" — or infer from conversation if clear.
   Also read `Projects/{name}/{name}-activity.md` for entries newer than the last `## [date]` in the
   session log (sessions that ended without `/brain end`, headless job runs) and fold them into this entry.
2. Append to `Projects/{name}/{name}-session-log.md` (format is a one-line summary header, optional bullets under it):
   ```
   ## [YYYY-MM-DD] | {summary}
   ```
3. Read `Projects/{name}/{name}-status.md` — update the "## Current" section only:
   - Under `### Done`: add what completed this session
   - Under `### Next Steps`: add/remove items; move finished ones to Done
   - Under `### Blocked By`: update blockers
   - Preserve the "## History" table — append a new row only if the phase changed
4. If a `Projects/{name}/{name}-agenda.md` exists, reconcile it: mark completed agenda items `done`, add any new tasks discovered this session as `todo`.
5. Append to `Claude/log.md`:
   ```
   ## [YYYY-MM-DD] | {project} | {one-line summary}
   ```
6. If any decisions were made, append to `Projects/{name}/{name}-decisions.md`:
   ```
   ## [YYYY-MM-DD] Decision: {X} | Rationale: {Y}
   ```
7. Run `sync --fix {name}` (the structural safety net): projects any loose notes the session
   wrote into `{name}.md`'s `## Documents`, repairs broken canonical links, and flags dated
   snapshots for archive. This is what keeps the vault self-consistent without relying on each
   write remembering to link — write freely, `end` projects the structure. (Supervised here at
   session end on purpose — not a per-turn hook.)
8. **Refresh generated views**: run
   `python "{{CLAUDE_PATH}}/skills/brain/scripts/brain.py" sync --no-git`. This journals the
   session so far, regenerates `projects-index` and `health`, and clears this project's "uncurated" warning.
   The scheduled `Brain Sync` task commits and pushes the vault; don't commit here.
9. **Refresh the repo pointer** — run the `pointer` subcommand logic for `{name}` (the working dir
   is the repo root). It regenerates the `BRAIN:POINTERS` block in the gitignored `CLAUDE.local.md`
   (idempotent — same inputs, same bytes). Gitignored, so there is no git-noise concern. Skip if
   there is no code repo.
10. Report: "Session saved to vault. sync: {N} notes indexed, {M} links repaired. Pointer refreshed (CLAUDE.local.md)."
