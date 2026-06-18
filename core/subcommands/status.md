## status

Show a quick health check of the memory system.

1. Read `Claude/projects-index.md` — list active projects
2. For each active project, read `Projects/{name}/{name}-status.md` — show phase and last updated
3. Glob `_raw/inbox/**/*.md` (exclude `.keep`) — count pending items per subfolder
4. Read last 3 lines of `Claude/log.md` — show recent activity
5. Output a compact summary:
   ```
   Projects:
     SMC-Research — Phase 2 | last session: YYYY-MM-DD
   
   Inbox:
     _raw/inbox/: N files
     _raw/inbox/SMC-Research/: N files
     _raw/inbox/Personal/: N files (locked)
   
   Recent activity:
     [last 3 log entries]
   ```
