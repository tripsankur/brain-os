## history

Mine `{{CLAUDE_PATH}}/projects/` conversation history and extract knowledge into the vault.

1. Glob `{{CLAUDE_PATH}}/projects/**/*.jsonl` — list available project session files
2. Ask user: "Which project history to mine?" and which date range (default: last 30 days)
3. For each selected JSONL file, read and extract:
   - Architectural decisions made
   - Domain concepts explained or discovered
   - Code patterns established
   - Problems solved and how
4. For each extracted item, determine if it already exists in the target project wiki:
   - If new: append to `Projects/{name}/{name}.md` under relevant section
   - If a decision: append to `Projects/{name}/{name}-decisions.md`
   - Mark provenance: `^[extracted from session YYYY-MM-DD]`
5. Report: "Mined {N} sessions. Added {M} items to {project} wiki."
