# /social-content — Instagram Content Pipeline
<!-- Orchestrator skill. Reads agent files from {{CLAUDE_PATH}}/skills/social-content/agents/. Agents are NOT slash commands. -->

Vault: `{{VAULT_PATH}}/Projects/social-content`

Run the subcommand passed as the first argument. If no argument given, run `status`.

## Subcommand dispatch

| Subcommand | What it does |
|------------|-------------|
| `run` | Execute full pipeline for a new brief |
| `approve` | Mark a run as approved and ready to post |
| `status` | Show pipeline status across all active runs |
| `brand-register` | Register a new brand in the brand registry |
| `brand-fork` | Fork an existing brand to create a new one |

## Living diagrams
Diagrams are maintained at `diagrams/` in the vault. **Update them when pipeline changes.**
- `diagrams/pipeline-flow.md` — full flow with gates and error paths
- `diagrams/agent-roster.md` — agent registry, responsibilities, planned agents
- `diagrams/brain-os-overview.md` — system architecture, skill map, sequence diagram, tier evolution

When a new agent is added or a gate changes: (1) update the relevant diagram, (2) add a row to the "Update log" table in that diagram.

## Pipeline stages (in order)

```
research → draft → critique (gate: 70, fact-check blocking) → format → approval
```

Critique is the single comprehensive review: quality scoring, fact-check (BLOCKING if incorrect claims), distribution signals, video brief, monetize signal. Everything in one pass.

---

## run {brand} {pillar} {topic} [format]

Execute the full pipeline: research → draft → critique → format → approval.

`format` defaults to `text_post`. Options: `text_post`, `video_script`.

**Step 1 — Validate brand**

Read `_brain/registry/brands.md`. Check that `{brand}` exists with `status: active`.
If not found, halt: "Brand '{brand}' not registered. Run `/social-content brand-register {brand}` first."

**Step 2 — Validate pillar**

Read `brands/{brand}/content-pillars.md`. Confirm `{pillar}` matches one of the 5 pillars (case-insensitive).
Valid: `claude-features`, `ai-education`, `brain-ai`, `startup-productivity`, `ai-shift`.
If invalid, list available pillars and halt.

**Step 3 — Create run**

Generate `run_id = {brand}-{YYYYMMDD}-{slug}` where slug is 3 words from topic, hyphenated, lowercase (e.g. `ankur-20260427-context-window-memory`).

Create vault directory `runs/{run_id}/`.

Write `runs/{run_id}/brief.md`:
```markdown
---
run_id: {run_id}
brand: {brand}
pillar: {pillar}
topic: {topic}
format: {text_post|video_script}
created: {YYYY-MM-DD}
status: in_progress
---

# Brief — {topic}

Brand: {brand}
Pillar: {pillar}
Format: {format}
Topic: {topic}
```

Write `runs/{run_id}/WORKLOG.md`:
```markdown
---
run_id: {run_id}
brand: {brand}
---

# WORKLOG — {run_id}

[{YYYY-MM-DD HH:MM}] orchestrator | run created | brand: {brand} | pillar: {pillar} | topic: {topic}
```

**Step 4 — Research stage**

Read `{{CLAUDE_PATH}}/skills/social-content/agents/research.md`.
Execute the research agent instructions with the context: `run_id`, `brand`, `pillar`, `topic`, `format`.

After execution, check `runs/{run_id}/WORKLOG.md` for `GATE FAIL`. If found, halt and report the reason to the user. Do not proceed to draft.

**Step 5 — Draft stage**

Read `{{CLAUDE_PATH}}/skills/social-content/agents/draft.md`.
Execute the draft agent instructions.

After execution, check WORKLOG for `GATE FAIL`. If found, halt and report reason. Do not proceed to critique.

**Step 6 — Critique stage**

Read `{{CLAUDE_PATH}}/skills/social-content/agents/critique.md`.
Execute the critique agent instructions.

After execution, read `runs/{run_id}/critique.md` frontmatter:
- If `verdict: blocked` → halt pipeline. Write `runs/{run_id}/approval.md` with `status: fact_check_blocked` and the blocking claims from critique.md. Report to user: "Critique blocked — incorrect claims must be corrected before proceeding. See runs/{run_id}/critique.md."
- If `verdict: pass` → proceed to format
- If `verdict: fail`:
  - Check WORKLOG for retry count. If this is attempt 1: re-run draft stage with critique's "Required revisions" section appended to brief context, increment retry counter in WORKLOG, re-run critique.
  - If this is attempt 2 (retry_max reached): escalate — write `runs/{run_id}/approval.md` with `status: needs_human_review` and the critique's required revisions. Report to user: "Draft failed critique after 2 attempts. Review at runs/{run_id}/approval.md."
  - Append to WORKLOG: `[timestamp] orchestrator | critique {pass|fail|blocked} | attempt: {N}`

**Step 7 — Format stage**

Read `{{CLAUDE_PATH}}/skills/social-content/agents/format.md`.
Execute the format agent instructions.

After execution, check WORKLOG for `GATE FAIL`. If found, halt and report reason.

**Step 8 — Create approval artifact**

Read `runs/{run_id}/final.md` (caption) and `runs/{run_id}/critique.md` (all review data).
Confirm `status: ready_for_approval` in final.md.

Write `runs/{run_id}/approval.md`:
```markdown
---
run_id: {run_id}
brand: {brand}
status: pending_approval
created: {YYYY-MM-DD}
---

# Approval — {topic}

**Brand**: {brand}
**Pillar**: {pillar}
**Format**: {format}
**Critique score**: {score}/100
**Fact-check**: PASS
**Distribution**: {ad_type} — {one-line from critique.md paid readiness rationale}

---

## Ready to post — Caption

{copy final.md caption verbatim}

---

## Video brief

**Format**: {face_on_camera|voiceover_visuals}
**Tier**: {N} — {tools}

{Copy Hook beat from critique.md video brief section}

---

## Distribution signals (from Critique)
Save: {N}/10 | Share: {N}/10 | Comment: {N}/10
Paid readiness: {ad_type}
{Copy paid readiness rationale from critique.md}

---

## Monetize signal (from Critique)
**Pain point**: {from critique.md}
**Format**: {format} | **Price**: ${range}
**MVL**: {one sentence}

---

## Actions
- Approve: change `status` to `approved` and run `/social-content approve {run_id}`
- Reject: change `status` to `rejected` and add notes under `## Rejection notes`
```

**Step 9 — Route escalation facts**

Read `runs/{run_id}/research.md` frontmatter. Check `ephemeral` flag.
Run `/brain route {run_id}` behavior: read escalation frontmatter and route durable facts to agent INBOX for later MEMORY.md promotion.

**Step 10 — Update WORKLOG and report**

Append to `runs/{run_id}/WORKLOG.md`:
```
[{YYYY-MM-DD HH:MM}] orchestrator | pipeline complete | score: {N}/100 | fact_check: pass | paid: {type} | status: pending_approval
```

Report to user:
```
Run {run_id} complete.

Critique: {N}/100 | Fact-check: PASS | Distribution: {ad_type}
Approval pending at: runs/{run_id}/approval.md
```

---

## approve {run_id}

Mark an approved run and record it.

1. Read `runs/{run_id}/approval.md` — confirm `status: approved`
2. Update `runs/{run_id}/brief.md` frontmatter: `status: approved`
3. Append to `runs/{run_id}/WORKLOG.md`:
   ```
   [{timestamp}] orchestrator | APPROVED | run complete
   ```
4. Run `/brain promote` logic for any INBOX facts from this run (durable, non-ephemeral research findings → MEMORY.md candidates)
5. Report: "Run {run_id} approved. Promote durable facts to MEMORY.md? (y/n)"

---

## status

Show the current state of all runs.

1. Glob `runs/*/brief.md` — list all runs
2. For each, read frontmatter: `run_id`, `brand`, `status`, `created`
3. For in-progress runs, check last WORKLOG line for current stage
4. Output:

```
Active runs:
  {run_id} | {brand} | {status} | last: {last WORKLOG line}

Pending approval:
  {run_id} | {brand} | score: {N}/100 | created: {date}

Approved:
  {run_id} | {brand} | {date}
```

---

## brand-register {name} {platform}

Register a new brand.

1. Check `_brain/registry/brands.md` — if `{name}` already exists, halt.
2. Create `brands/{name}/` directory
3. Write placeholder `brands/{name}/brand-voice.md`:
   ```markdown
   # Brand Voice — {name}
   > Run /social-content brand-register {name} and complete this file before running pipeline.
   
   ## Identity
   (describe the brand)
   
   ## Audience
   (target audience)
   
   ## Tone
   (tone and style)
   
   ## What to avoid
   (patterns to reject)
   
   ## Platform — Instagram v1
   - Caption ≤ 2200 characters
   - Hashtags at end, 10–15
   ```
4. Write placeholder `brands/{name}/content-pillars.md`
5. Append row to `_brain/registry/brands.md`:
   ```
   | {name} | brands/{name}/brand-voice.md | draft | {YYYY-MM-DD} | {platform} |
   ```
6. Report: "Brand '{name}' registered (status: draft). Complete brands/{name}/brand-voice.md before running pipeline."

---

## brand-fork {source} {new-name}

Fork an existing brand to create a new one.

1. Read `_brain/registry/brands.md` — confirm `{source}` exists with `status: active`.
2. Check `{new-name}` does not already exist in registry.
3. Copy `brands/{source}/brand-voice.md` → `brands/{new-name}/brand-voice.md`
4. Copy `brands/{source}/content-pillars.md` → `brands/{new-name}/content-pillars.md`
5. Update frontmatter in both copied files: replace `{source}` with `{new-name}`.
6. Append to `_brain/registry/brands.md`:
   ```
   | {new-name} | brands/{new-name}/brand-voice.md | draft | {YYYY-MM-DD} | instagram |
   ```
7. Report: "Brand '{new-name}' forked from '{source}'. Edit brands/{new-name}/brand-voice.md to differentiate before running pipeline."
