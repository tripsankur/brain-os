# Projects Index
> See also: [[workflow]] | [[preferences]] | [[log]]
> The portfolio view. `/brain status` reads this; `/brain new-project` appends to it.

## Active Projects

| Project | Folder | Phase | Last Updated |
|---------|--------|-------|--------------|

## Project Template
Each project lives in `Projects/{name}/` (prefixed folder-note pattern):
- `{name}.md` — knowledge wiki (folder note; visible in the graph)
- `{name}-status.md` — current phase, done, blockers, next
- `{name}-decisions.md` — decisions + rationale (append-only)
- `{name}-session-log.md` — what happened each session (append-only)
- `{name}-agenda.md` — prioritized backlog

## Adding a project
Run `/brain new-project {name}` — it scaffolds the folder and adds the row above.
