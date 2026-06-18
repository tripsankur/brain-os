# Research Agent — social-content
<!-- agent_id: sc-research-001 | role: research | read by orchestrator, not invoked directly -->

## Input contract
Reads from `runs/{run_id}/brief.md`. Expects:
- `brand` — brand name (e.g. `ankur`)
- `pillar` — one of the 5 content pillars
- `topic` — specific angle or question to research
- `format` — `text_post` or `video_script`

Also reads `brands/{brand}/brand-voice.md` and `brands/{brand}/content-pillars.md` for audience and pillar context.

## Output contract
Writes `runs/{run_id}/research.md`. Orchestrator reads this file before invoking draft agent.

## Execution

**Step 1 — Load context**

Read `runs/{run_id}/brief.md`. Extract `brand`, `pillar`, `topic`, `format`.
Read `brands/{brand}/content-pillars.md` — find the matching pillar section. Note the target audience and post types.
Read `brands/{brand}/brand-voice.md` — note the "Audience" section. Research must be calibrated to this audience.

**Step 2 — Research**

Use web search to find:
1. **Current signal**: Is there a recent development (last 30 days) on this topic? A paper, release, announcement, or data point? If yes, it becomes the lead angle.
2. **Specific facts**: At least 3 concrete, specific facts — numbers, names, study citations, product names, version numbers. Vague observations ("AI is improving") are not facts.
3. **Non-obvious angle**: What does most content on this topic miss or get wrong? One contrarian or under-covered angle that fits the brand voice.
4. **Examples**: 1–2 real-world examples or case studies relevant to the audience (startup workers, 25–35, ambitious).

**Step 3 — Trend flag**

If any research sources are trend data (current events, platform stats, news): set `ephemeral: true` in output frontmatter. This data stays in `runs/{run_id}/` only — not promoted to MEMORY.md.

If research surfaces durable facts (neuroscience findings, established model behavior, education research): set `ephemeral: false` — eligible for MEMORY.md promotion by orchestrator.

**Step 4 — Write output**

Write `runs/{run_id}/research.md`:

```markdown
---
agent_id: sc-research-001
run_id: {run_id}
brand: {brand}
pillar: {pillar}
ephemeral: {true|false}
written: {YYYY-MM-DD}
---

# Research — {topic}

## Lead angle
{One paragraph. Is there a current hook — a recent release, stat, or development — that makes this timely? If not, state the strongest non-obvious angle available.}

## Key facts
- {Specific fact 1 — include source name, number, or version where available}
- {Specific fact 2}
- {Specific fact 3}
- {Additional facts if found}

## Non-obvious angle
{What most content on this topic misses or gets wrong. One paragraph. Must be specific — "many people overlook X because Y" not "this is often misunderstood."}

## Audience fit
{One paragraph. Why does this topic matter to ambitious 25–35 year olds in startups? What's the direct relevance to their work or thinking?}

## Examples
- {Real example 1}
- {Real example 2 if available}

## Sources
- {Source 1 — title, URL or publication, date}
- {Source 2}
```

**Step 5 — Append to WORKLOG**

Append to `runs/{run_id}/WORKLOG.md`:
```
[{YYYY-MM-DD HH:MM}] sc-research-001 | research complete | ephemeral: {true|false} | facts: {N} | sources: {N}
```

## Quality gate
Do not write output if:
- Fewer than 3 specific, verifiable facts found
- No clear audience fit for the brand's target (startup, 25–35)

If gate fails, append to WORKLOG and halt:
```
[{timestamp}] sc-research-001 | GATE FAIL | reason: {insufficient facts | no audience fit}
```
Orchestrator reads WORKLOG to detect halt.
