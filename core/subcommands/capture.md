## capture

Save the key insights from the current conversation as a permanent vault note, with full graph linkage.

**Steps:**

### 1 — Extract insights

Read the conversation and identify:
- Core concepts or discoveries not already in the project wiki
- Decisions made with their rationale
- Open questions or next steps

### 2 — Determine target

- If insights belong in an existing page → append to `{{VAULT_PATH}}/Projects/{name}/{name}.md` (the project wiki, not `index.md`)
- If they're standalone → proceed to step 3

### 3 — Write the capture file

Write to `{{VAULT_PATH}}/Projects/{name}/captures/YYYY-MM-DD-{slug}.md`:

```markdown
# {Title}
> [[{name}]] | [[captures]]
Date: YYYY-MM-DD
Session: {brief context}

{extracted content}

## Open Questions
{any unresolved questions — omit section if none}
```

The `> [[{name}]] | [[captures]]` backlink line is mandatory — it connects the capture to the project wiki and the captures hub in the Obsidian graph.

### 4 — Update captures hub

Read `{{VAULT_PATH}}/Projects/{name}/captures/captures.md`:
- If the file exists: append a row to the table: `| YYYY-MM-DD | {Title} | [[YYYY-MM-DD-{slug}]] |`
- If the file does not exist: create it:

```markdown
# {Name} — Captures
> [[{name}]] | [[{name}-session-log]]
> Append-only index of captured insights.

| Date | Title | Slug |
|------|-------|------|
| YYYY-MM-DD | {Title} | [[YYYY-MM-DD-{slug}]] |
```

### 5 — Report

```
Captured to Projects/{name}/captures/YYYY-MM-DD-{slug}.md
Hub updated: Projects/{name}/captures/captures.md
```
