# Tests

Brain OS test suite. Runs on clean checkout — no personal vault required.

## Structure

```
tests/
├── fixtures/
│   ├── test-vault/       — minimal Obsidian-compatible vault for test runs
│   │   └── Claude/       — global memory layer (agents.md, projects-index.md, etc.)
│   └── test-claude/      — minimal ~/.claude equivalent for install tests
│       └── commands/
├── unit/                 — fast, no install required
│   ├── dispatch-table.sh — every subcommand in brain.md points to an existing file
│   ├── registry-schema.sh — agents.md and agents-archive.md match expected schema
│   └── token-scan.sh     — no {{TOKEN}} remaining in installed files after install
├── e2e/                  — requires running install script against test fixtures
│   ├── install.sh        — install → verify token resolution → run /brain status
│   └── new-project.sh    — /brain new-project test-project → assert directory tree
└── run-all.sh            — run all tests, report pass/fail

## Running

# Unit tests only (fast, no install)
./tests/run-all.sh --unit

# Full suite (runs install against test fixtures)
./tests/run-all.sh

# Single test
./tests/unit/dispatch-table.sh
```

## QA gates

These checks run in CI on every push to main:

| Check | What it verifies |
|-------|-----------------|
| Dispatch table integrity | Every entry in brain.md dispatch table → file exists |
| Registry schema | agents.md fields match required schema |
| Token scan | No `{{TOKEN}}` in installed files, no `C:\Users` in core/ |
| Module manifest | module.json fields present and valid |
| e2e install | Install script completes against test fixtures |
| e2e new-project | /brain new-project creates correct vault structure |
