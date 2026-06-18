## ingest

Process `_raw/inbox/` manually on demand. Use when you've dropped files and want to route them now without waiting for next session start.

**Step 1 — Discover files**: Glob ALL files in `_raw/inbox/` recursively (exclude `.keep`). Do not filter by extension.

**Step 2 — Determine routing scope per file**:
- File is under `_raw/inbox/{project-name}/` → route to that project
- File is under `_raw/inbox/Personal/` → Personal scope (check access below)
- File is under `_raw/inbox/` root → infer from file content/name

**Step 3 — Personal access gate**: If any file is in `_raw/inbox/Personal/` or inferred as personal content, check whether the user has granted Personal access this session. If not, skip those files and report them as "skipped (Personal locked)".

**Step 4 — Process each file by type**:

| Extension | Action |
|-----------|--------|
| `.md`, `.txt`, `.csv`, `.json`, `.yaml` | Read full content → infer content type → route per workflow.md rules |
| `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp` | Read visually → write caption as asset note (see below) |
| `.pdf` | Read up to 20 pages → summarize → route as `.md` summary |
| `.xlsx`, `.xls`, `.docx`, `.pptx` | Cannot read — log existence only (see below) |
| `.mp4`, `.mov`, `.avi`, other video | Cannot read — log existence only (see below) |
| Any other | Treat as unreadable — log existence only |

**Asset note** (for images/PDFs): write `_raw/processed/YYYY-MM-DD-{stem}.md`:
```markdown
# {filename}
Type: image | Date: YYYY-MM-DD | Source: {original inbox path}

{visual description or PDF summary}
```
Then route this `.md` asset note to destination.

**Existence log** (for binary/video files that can't be read): move file to `_raw/processed/YYYY-MM-DD-{filename}` and append to destination index.md:
```
- [{filename}](_raw/processed/YYYY-MM-DD-{filename}) — {inferred description from filename/folder} | needs manual extraction | ingested YYYY-MM-DD
```

**Step 5 — Write summary bullet to destination index**: After routing ANY file (readable or not), append to the destination's `index.md` (or `Personal/personal.md` for Personal scope):
```
- [[{stem}]] — {one-line summary} (ingested YYYY-MM-DD)
```
This is what `/brain recall` reads — routed content is immediately recallable.

**Step 6 — Move source file**: Move original file from inbox to `_raw/processed/YYYY-MM-DD-{filename}`.

**Step 7 — Report**:
```
Processed N files:
  ✓ {filename} → {destination} — {one-line summary}
  ✓ {filename} → {destination} — logged (binary, needs manual extraction)
  ✗ {filename} → skipped (Personal locked)
```
