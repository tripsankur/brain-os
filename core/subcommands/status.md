## status

Show the health of the memory system.

1. Run the engine. It sweeps transcripts, refreshes the generated views and health, and does not touch git:
   ```
   python "{{CLAUDE_PATH}}/skills/brain/scripts/brain.py" sync --no-git
   ```
2. Read `{{VAULT_PATH}}/Claude/health.md` (the AUTO block). It lists:
   - warnings (uncurated sessions, failed scheduled tasks, stale live jobs, repos without git, unregistered folders)
   - info lines (backup state, unmapped sessions)
3. Read the AUTO block of `{{VAULT_PATH}}/Claude/projects-index.md` and show the Live and Active tables.
4. Glob `_raw/inbox/**/*.md` (exclude `.keep`) and count pending items per subfolder. `Personal/` is locked unless access is granted.
5. Output a compact summary: health verdict, the warnings, Live/Active projects with phase and last activity, inbox counts. For each warning, propose the fix; don't apply it without the user's go.
