## init

Bootstrap a fresh Brain OS vault — the in-session equivalent of the installer's `--init-vault`.
Use this when the `/brain` skills are installed but the vault has no `Claude/` hub yet (so
`/brain start`/`status` have nothing to read).

Most users get this for free: the installer runs the same bootstrap when it detects an empty
vault. `/brain init` is for the "skills installed, vault still empty" case, or to (re)seed a hub.

## Usage

```
/brain init            # scaffold the vault skeleton from the shipped templates
/brain init --force    # also (re)create any hub file that is missing (never overwrites existing)
```

## Execution

1. Resolve the vault root from config/context (`{{VAULT_PATH}}`).
2. **Source = the deployed templates** (single source of truth): `{{CLAUDE_PATH}}/brain-templates/vault/`.
   The installer ships these so `/brain init` works even without the repo checked out. If the
   templates dir is missing, tell the user to re-run the installer.
3. Copy the template tree into the vault, **idempotently — never overwrite an existing file**:
   - `Claude/workflow.md`, `Claude/preferences.md`, `Claude/projects-index.md`, `Claude/log.md`,
     `Claude/agents.md`
   - `_raw/inbox/.keep`, `Projects/.keep`
4. Report what was created vs already present:
   ```
   Vault bootstrapped at {{VAULT_PATH}}:
     + Claude/workflow.md
     + Claude/projects-index.md
     ...
   (existing files left untouched)
   ```
5. Print the two finishing steps:
   - **Personalize** `Claude/preferences.md` (it ships as a template with placeholders).
   - **Add the session-start hook** so vault context is injected automatically every session
     (see README → "Session hook"). Until then, run `/brain start` manually.
6. Suggest the next move: `/brain new-project {name}` to create the first project.

## Design notes
- One source of truth: the templates in the repo are shipped to `{{CLAUDE_PATH}}/brain-templates/`
  at install; the installer's `--init-vault` and this subcommand both copy from there, and the test
  fixtures derive from the same seed. No hub content is authored inline in a script (that would drift).
- Idempotent by construction — safe to run on an existing vault; it only fills gaps.
