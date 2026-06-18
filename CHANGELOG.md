# Changelog

All notable changes to Brain OS will be documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

---

## [Unreleased] — v0.1.0

### Added
- Core `/brain` skill with 13 subcommands: start, end, capture, ingest, history, status, new-project, recall, agent-register, route, promote, sync, diagram
- `social-content` module: 4-agent pipeline (research → draft → critique → format → approval)
- 5-part critique agent: quality scoring, fact-check (blocking), distribution signals, video brief, monetize signal
- Config system: `brain-os.config.json` with vault path, endpoint, per-operation model selection
- Install scripts: `install.sh` and `install.ps1`
- Test suite: dispatch table integrity, registry schema, vault scaffolding, e2e install
- GitHub Actions CI

---
