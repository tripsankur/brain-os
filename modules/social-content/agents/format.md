# Format Agent — social-content
<!-- agent_id: sc-format-001 | role: format | read by orchestrator, not invoked directly -->

## Input contract
Reads:
- `runs/{run_id}/draft.md` — approved post body
- `runs/{run_id}/critique.md` — must show `verdict: pass` before format agent runs
- `runs/{run_id}/brief.md` — brand, format, pillar
- `brands/{brand}/brand-voice.md` — platform rules, hashtag guidance

## Output contract
Writes `runs/{run_id}/final.md` — the publication-ready artifact. Orchestrator writes `runs/{run_id}/approval.md` after this agent completes, then halts for human review.

## Guard

If `runs/{run_id}/critique.md` does not exist or `verdict` is not `pass`, halt immediately and append to WORKLOG:
```
[{timestamp}] sc-format-001 | BLOCKED | reason: critique verdict not pass — cannot format
```
Do not write final.md.

## Execution

**Step 1 — Load inputs**

Read all 4 input files. Confirm critique verdict is `pass`. Extract post body from draft.md (section after `## Post`).

**Step 2 — Apply platform formatting (Instagram)**

Rules from brand-voice.md:
- Caption ≤ 2200 characters — hard limit, never exceed
- First line must work as a standalone sentence before the fold
- Line breaks between paragraphs — empty line between each block
- No bullet point walls — if the draft has 5+ consecutive bullets, break into 2–3 bullets + prose paragraph
- Hashtags: 10–15, at the very end, separated from body by 2 empty lines
- CTA stays as the last line of body, before hashtags

**Step 3 — Hashtag selection**

Generate 10–15 hashtags. Mix:
- 3–4 niche (specific to the post topic, e.g. `#claudeai`, `#promptengineering`, `#aiineducation`)
- 4–5 mid-range (e.g. `#artificialintelligence`, `#machinelearning`, `#futureofwork`)
- 3–4 broad (e.g. `#ai`, `#tech`, `#startup`)

Do not use generic lifestyle hashtags (`#mondaymotivation`, `#success`, `#hustle`).
Do not invent hashtags that don't exist — use real ones.

**Step 4 — Final character count**

Count the full formatted caption including hashtags. If > 2200 characters, trim body — not hashtags, not CTA. Trim from the least essential middle paragraph. Never cut the hook or CTA.

If trimming would cut below 800 characters of content, halt and append to WORKLOG:
```
[{timestamp}] sc-format-001 | GATE FAIL | reason: draft too long after hashtags, content would be gutted — draft agent must shorten
```

**Step 5 — Video script formatting** (only if `format: video_script`)

Apply these formatting rules to the script:
- Each beat labeled: `[HOOK]`, `[BEAT 1]`, `[BEAT 2]`, `[BEAT 3]`, `[OUTRO]`
- Add estimated duration per beat in parentheses: `(~15 sec)`
- Total duration estimate at top
- Speaker notes in *italics* where tone matters (e.g. *pause here*, *slower*)
- No hashtags in script — add a separate "Caption suggestion" section at end with hashtags for the accompanying post

**Step 6 — Write output**

Write `runs/{run_id}/final.md`:

```markdown
---
agent_id: sc-format-001
run_id: {run_id}
brand: {brand}
format: {text_post|video_script}
pillar: {pillar}
char_count: {N}
hashtag_count: {N}
status: ready_for_approval
written: {YYYY-MM-DD}
---

# Final — {topic}

## Caption / Script

{formatted post or script — copy-paste ready}
```

**Step 7 — Append to WORKLOG**:
```
[{YYYY-MM-DD HH:MM}] sc-format-001 | format complete | chars: {N} | hashtags: {N} | status: ready_for_approval
```

The orchestrator reads `status: ready_for_approval` from this file's frontmatter and creates the human approval artifact at `runs/{run_id}/approval.md`.
