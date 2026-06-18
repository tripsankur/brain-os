# test-claude

Minimal `~/.claude/` equivalent for Brain OS install tests.

This directory is the target for `./tests/e2e/install.sh` — the e2e test runs install.sh
pointing `claude_install_path` here and verifies that all files land correctly with
tokens resolved.

Contents are written by the test and cleaned up after. Do not add permanent files here.
