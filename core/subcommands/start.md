## start

Load session context for the active project.

1. Read `Claude/preferences.md` and `Claude/projects-index.md` (already injected by hook — skip if visible in context)
2. Ask user: "Which project are we working on today?" if not clear from context
3. Read `Projects/{name}/{name}-status.md` — report current phase and next steps in 3 bullet points
   - Also read `Projects/{name}/{name}-agenda.md` if present — report the top 1–3 `todo` agenda items
4. Glob `_raw/inbox/` root for any `.md` files (exclude `.keep`) — if found, process each:
   - Read the file, infer type and target project from content
   - Route per inbox processing rules in `Claude/workflow.md`
   - Move to `_raw/processed/YYYY-MM-DD-{original-filename}`
5. Glob `_raw/inbox/{project-name}/` — if `.md` files found, process same way
6. Report: "Session ready. Phase X. N inbox items processed."
