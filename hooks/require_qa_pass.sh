#!/usr/bin/env bash
# Block Stop unless QA most recently logged a pass (v0.2).
set -euo pipefail
STATE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.qa_state"
[ -f "$STATE" ] || exit 0  # no study activity this session
grep -q '^pass ' "$STATE" && exit 0
echo '{"decision":"block","reason":"QA has not passed yet. Run: python3 scripts/study.py qa --db <study.sqlite>"}'
exit 0
