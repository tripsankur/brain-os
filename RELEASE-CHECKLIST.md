# Release Checklist — making Brain OS public

Status of each gate as of the last update. **Do not `git push` to a public remote until every
BLOCKER is cleared.** The repo currently has **no remote** — keep it that way until ready.

## ✅ Done / verified

- **Portability proven.** `install.ps1` runs clean to an arbitrary target; a fresh install leaves
  **0 unresolved tokens** and no hardcoded user paths in the installed files. `install.ps1` parse
  bug (non-ASCII em-dash) fixed.
- **README** rewritten to current reality (Journal/Map/Hands, graphify optional, real install flow).
- **CONTRIBUTING.md** added. **LICENSE** = MIT.
- **`brain-os.config.json`** (vault path + any keys) is gitignored — not in the tree.

## ⛔ BLOCKERS before public

1. **Personal data in working tree.** A clean-install scan found **~53 `ankur` references**, almost
   all in `modules/social-content/` (brand examples like `brand ankur`, run ids `ankur-YYYYMMDD-…`,
   the "Ankur here" voice example) plus the README clone URL.
   - **Action:** genericize the social-content module examples to `your-brand` / `example`; keep the
     clone URL a placeholder. Re-run the scan: `git grep -i ankur -- . ':(exclude)LICENSE'` → expect
     only the LICENSE author line.
2. **Personal data in `tests/fixtures/test-vault/Claude/`.** `preferences.md`, `log.md`,
   `projects-index.md` fixtures may carry real vault content.
   - **Action:** replace fixture content with synthetic `test-project` data.
3. **Git history contains the above.** Scrubbing the working tree does **NOT** remove personal data
   from history (commits `d304eba`, `7aaa332`, `054d10e`, …). Publishing exposes full history.
   - **Action (pick one), done AFTER 1–2 are scrubbed:**
     - **Fresh re-init (simplest, recommended for a first public release):** `rm -rf .git && git init`
       then one clean `Initial public release` commit. Loses the private build history (fine — it was
       a personal build log).
     - **History rewrite:** `git filter-repo` to strip the offending strings/files across all commits.
4. **`docs/brain-map-spec.md`** is the retired heuristic map design — superseded by graphify. Redirect
   or delete it so a reader isn't misled (handled: file now points to `brain-graphify-loops.md`).

## Final publish steps (the user's action — not automated)

These are outward-facing + need your GitHub auth; the assistant will not perform them:
1. Create the GitHub repo (private first if you want a final review).
2. `git remote add origin <url>` && `git push -u origin main`.
3. Verify CI (`.github/workflows/ci.yml`) passes on the pushed branch.
4. Flip to public only after the BLOCKERS above are cleared and you've eyeballed the rendered README.

## Nice-to-have before/at release

- `CHANGELOG.md` entry for the release tag.
- Tag `v0.1.0` and write release notes.
- Confirm `./tests/run-all.sh` passes on a fresh clone.
