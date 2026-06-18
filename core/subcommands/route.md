## route {project} {run_id}

After a pipeline run, read each agent's escalation frontmatter and route facts to the correct destinations.

**Arguments**: `{project}` — project name, `{run_id}` — run folder name (e.g. `run-20260427-lifestyle-hooks`)

**Steps**:

1. Read all output files in `{vault}/Projects/{project}/runs/{run_id}/`:
   - `research.md`, `draft.md`, `critique.md`, `formatted.md`

2. For each file, extract YAML frontmatter block containing `escalate:` list.

3. For each escalation item:
   - If `ephemeral: true` → write to `runs/{run_id}/sources.md` only. Do NOT write to any MEMORY.md.
   - If `ephemeral: false` → candidate for durable memory (check promotion criteria in `_brain/policies/promotion.md`)
   - For each agent in `notify_agents`: append fact to `{vault}/Projects/{project}/agents/{agent}/INBOX.md`:
     ```
     ## {today} | from:{source_agent} | run:{run_id}
     {fact}
     confidence: {confidence} | freshness: {freshness}
     ```

4. Append durable facts to emitting agent's OUTBOX.md:
   ```
   ## {today} | run:{run_id}
   {fact}
   routed_to: [{notify_agents}]
   ```

5. Append event to `{vault}/Projects/{project}/_brain/runtime/events-{YYYY-MM}.md`:
   ```
   ## {timestamp} | route | run:{run_id}
   Facts routed: {N}. Ephemeral: {M}. Notified agents: {list}.
   ```

6. Report: "Routed {N} facts. {M} ephemeral (sources.md only). {K} durable (pending promotion check)."
