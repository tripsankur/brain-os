## recall {topic}

Surface connected context from the vault by traversing the wikilink graph. Use this when you need to recall domain knowledge, past decisions, or architecture for a given topic — without doing a keyword search.

**Determine scope**:
- `/brain recall {topic}` → use the active project from context
- `/brain recall {topic} personal` → scope to `Personal/` (requires Personal access this session)
- `/brain recall {topic} {project-name}` → scope to that specific project
- If scope unclear, ask.

**Execution**:

1. Identify root node:
   - Project scope → `Projects/{name}/{name}.md` (the prefixed wiki root)
   - Personal scope → `Personal/personal.md`
2. Scan for `[[wikilinks]]` in the file — collect all linked filenames within `Projects/{name}/`
3. For each wikilink that matches or is related to `{topic}` (by name or section heading):
   - Read that file
   - Scan its wikilinks — follow one more level (level 2), staying within `Projects/{name}/`
   - Read any level-2 files that are also relevant to `{topic}`
4. Also scan `Projects/{name}/{name}-decisions.md` directly — any decision mentioning `{topic}` is always included
5. Also scan `Projects/{name}/captures/` directly — read `captures/captures.md` (if present) plus any `captures/*.md` whose title or slug matches `{topic}`. Captures are first-class recall sources, not just graph-linked notes.
6. Compose and output a context cluster:
   ```
   ## Recall: {topic} (project: {name})
   
   ### From {name}.md
   {relevant excerpts}
   
   ### From {linked-file}.md
   {relevant excerpts}
   
   ### Decisions
   {any decisions mentioning the topic}
   
   ### Captures
   {any matching captures}
   
   ### Open questions
   {any unresolved questions found}
   ```
7. If nothing found: report "No context found for '{topic}' in {name}. Consider running /brain capture after discussing it this session."

**Scope rules**:
- Project scope: stay within `Projects/{name}/` — no cross-project contamination
- Personal scope: stay within `Personal/` — requires Personal access granted this session
- Max depth: 2 levels from root node
- If a wikilink target file doesn't exist, skip silently
- `Claude/` hub files (`workflow.md`, `preferences.md`) are out of scope — procedural, not domain knowledge
