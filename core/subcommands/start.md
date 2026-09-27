## start

Load session context for the active project.

The SessionStart hook (`brain.py session-start`) has usually injected context already. That context covers the project resolved from the cwd, its phase, a status excerpt, uncurated sessions and health warnings. Use it rather than re-reading those files.

1. Project: take it from the hook's `Project:` line. If the hook said "No vault project mapped", ask: "Which project are we working on today?"
   - If the project is new, offer `/brain new-project`.
   - If it exists under another name, offer a row in `{{VAULT_PATH}}/Claude/registry.md`.
2. Read `Projects/{name}/{name}-status.md`. Report the current phase and next steps in 3 bullet points.
   - If `Projects/{name}/{name}-agenda.md` exists, also report the top 1–3 `todo` agenda items.
   - If `Projects/{name}/{name}-auto-status.md` exists (a mirror of a job's own status), report its headline and flag any disagreement with the curated status.
3. If the hook reported **uncurated sessions**, read `Projects/{name}/{name}-activity.md` for the entries newer than the last session-log date. Offer to fold them into the curated notes now, using the `end` steps with the activity entries as the source.
4. Glob `_raw/inbox/` root for any `.md` files (exclude `.keep`). If found, process each:
   - Read the file, infer type and target project from content
   - Route per inbox processing rules in `Claude/workflow.md`
   - Move to `_raw/processed/YYYY-MM-DD-{original-filename}`
5. Glob `_raw/inbox/{project-name}/`. If `.md` files are found, process them the same way.
6. Report: "Session ready. Phase X. N inbox items processed. M uncurated sessions."
