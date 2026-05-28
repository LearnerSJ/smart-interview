#!/usr/bin/env bash
# Block Stop unless qa-validator most recently logged a pass.
set -euo pipefail
STATE="$CLAUDE_PROJECT_DIR/hooks/.qa_state"
[ -f "$STATE" ] || exit 0  # no workbook activity this session
grep -q '^pass ' "$STATE" && exit 0
echo '{"decision":"block","reason":"qa-validator has not passed yet. Run: python3 scripts/workbook.py qa --path <workbook>"}'
exit 0
