## end

Write session back to vault. Run this at the end of every meaningful session.

**Filename convention**: every project file is PREFIXED with the project name — `{name}.md` (wiki root), `{name}-status.md`, `{name}-session-log.md`, `{name}-decisions.md`, `{name}-agenda.md`. Never write unprefixed `status.md`/`index.md`; the read/recall paths expect the prefixed names and will miss anything else.

**Wikilink rule**: every file written or appended must include `[[wikilinks]]` to related files within the same project. At minimum, each project file links to its siblings: `[[{name}]]`, `[[{name}-status]]`, `[[{name}-decisions]]`, `[[{name}-session-log]]`, `[[{name}-agenda]]`. The hub files (`Claude/workflow.md`, `Claude/log.md`, `Claude/preferences.md`, `Claude/projects-index.md`) link to each other.

1. Ask user: "Summarize what we did this session in one sentence" — or infer from conversation if clear
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
8. Report: "Session saved to vault. sync: {N} notes indexed, {M} links repaired."
