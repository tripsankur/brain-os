## promote {project} {agent} {fact_ref}

Promote a fact from an agent's INBOX or OUTBOX to durable MEMORY.md, subject to promotion criteria.

**Arguments**: `{project}` — project name, `{agent}` — agent role (e.g. `draft`), `{fact_ref}` — fact identifier or "all-pending"

**Steps**:

1. Read `{vault}/Projects/{project}/_brain/policies/promotion.md` — load promotion criteria:
   - Minimum confidence: medium or high
   - Must not be ephemeral
   - Must be referenced in ≥ 2 runs OR manually flagged by orchestrator

2. If `{fact_ref}` is "all-pending":
   - Read agent's `INBOX.md` — find all facts not yet marked as promoted
   - Evaluate each against promotion criteria

3. For each qualifying fact:
   - Append to `{vault}/Projects/{project}/agents/{agent}/MEMORY.md`:
     ```
     ## {today} | {fact_source}
     {fact}
     Source: {run_id} | Confidence: {confidence}
     ```
   - Mark fact in INBOX.md as `[promoted: {today}]`

4. If fact does NOT qualify: report reason (ephemeral, low confidence, single-run only).

5. Append to events ledger:
   ```
   ## {timestamp} | promote | {agent}
   {N} facts promoted to MEMORY.md.
   ```

6. Report: "Promoted {N} facts to {agent}/MEMORY.md. {M} rejected (see reasons above)."
