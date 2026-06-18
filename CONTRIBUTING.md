# Contributing to Brain OS

Thanks for your interest. Brain OS is a set of Markdown skill files + a token-resolving installer,
so most contributions are documentation, subcommands, or modules — not heavy code.

## Ground rules

- **No hardcoded paths.** Every path in `core/` and `modules/` must use a token (`{{VAULT_PATH}}`,
  `{{CLAUDE_PATH}}`, `{{REPO_PATH}}`). The `token-scan` test enforces this.
- **No personal data.** No real names, vault paths, API keys, or private content in committed files
  (including `tests/fixtures/`). Use generic placeholders (`example`, `your-brand`, `/path/to/vault`).
- **Keep the canonical layout.** Project files are prefixed folder-notes
  (`{name}.md`, `{name}-status.md`, …). Don't introduce unprefixed `status.md`/`index.md`.

## Dev setup

```bash
git clone <your-fork-url> brain-os && cd brain-os
cp config/brain-os.config.example.json brain-os.config.json   # gitignored
./tests/run-all.sh
```

## Tests (must pass before a PR)

```bash
./tests/unit/dispatch-table.sh     # every subcommand in brain.md points to a real file
./tests/unit/token-scan.sh         # no hardcoded paths / unresolved tokens
./tests/unit/registry-schema.sh    # registry frontmatter valid
./tests/unit/module-manifest.sh    # module.json fields valid
./tests/e2e/new-project.sh         # scaffolding produces the canonical tree
```

## Adding a subcommand

1. Write `core/subcommands/{name}.md` (instructions the assistant executes).
2. Add a row to the dispatch table in `core/brain.md` and the "Available:" list.
3. Re-run `dispatch-table.sh`.

## Adding a module

See `docs/creating-a-module.md`. A module is `modules/{name}/{name}.md` + `agents/` + `module.json`,
and registers itself on install. Strip all personal data; use `{{VAULT_PATH}}/Projects/{name}/` tokens.

## Commit style

Conventional, imperative subject. Keep skill-file changes and code/test changes separate where
practical. End commit messages with a co-author trailer if pair-authored.

## PRs

- One concern per PR. Describe the user-facing behavior change.
- Note any new prerequisite (e.g. a command that needs `graphify`).
- Confirm `./tests/run-all.sh` passes on a clean checkout.
