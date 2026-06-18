## agent-register {project} {role}

Register a new agent in the project's `_brain/registry/agents.md` and create its sub-brain folder.

**Arguments**: `{project}` — project name (e.g. `social-content`), `{role}` — agent role (e.g. `research`)

**Generate immutable agent_id**: `{project-prefix}-{role}-{3-digit-seq}` (e.g. `sc-research-001`). Read existing agents.md to find next sequence number.

**Steps**:

1. Read `{vault}/Projects/{project}/_brain/registry/agents.md` — check if role already registered. If yes, report and stop.

2. Determine project prefix (first two letters of each word, max 4 chars): `social-content` → `sc`, `smc-research` → `sr`

3. Assign next sequence: read existing agents, find highest seq for this role, increment.

4. Create agent sub-brain folder at `{vault}/Projects/{project}/agents/{role}/`:
   - Write `PROFILE.md` from template (see below)
   - Write empty `MEMORY.md`: `# {Role} Agent — Memory\n> Durable patterns only. No ephemeral trend data.\n`
   - Write empty `INBOX.md`: `# {Role} Agent — Inbox\n> Append-only. Facts routed from other agents.\n`
   - Write empty `OUTBOX.md`: `# {Role} Agent — Outbox\n> Append-only. Facts emitted by this agent.\n`
   - Write empty `WORKLOG.md`: `# {Role} Agent — Work Log\n> One entry per invocation.\n`

5. Append to `{vault}/Projects/{project}/_brain/registry/agents.md`:
   ```
   | {agent_id} | {role} | active | {today} | claude-sonnet-4-6 |
   ```

6. Report: "Registered {agent_id} at agents/{role}/. PROFILE.md written."

**PROFILE.md template**:
```yaml
---
agent_id: {agent_id}
role: {role}
project: {project}
model_policy:
  provider: claude
  model: claude-sonnet-4-6
  web_search: false
memory_scope: project
status: active
created: {today}
subscriptions: []
---

# {Role} Agent Profile
> Part of project: {project}
> See also: [[MEMORY]] | [[WORKLOG]]
```
