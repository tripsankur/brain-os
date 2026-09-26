#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PY=$(command -v python3 >/dev/null 2>&1 && python3 -c "" 2>/dev/null && echo python3 || echo python)
PYTHONDONTWRITEBYTECODE=1 "$PY" "$REPO_ROOT/tests/unit/brain_engine_test.py"
