#!/usr/bin/env bash
# v0.2: the .xlsx is a regenerable VIEW of the study ledger. Any .xlsx write must
# go through scripts/study.py (export), never hand-edited or written by other tools.
set -euo pipefail
INPUT="$(cat)"
CMD="$(echo "$INPUT" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d.get("tool_input",{}).get("command",""))' 2>/dev/null || echo "")"
if echo "$CMD" | grep -Eq '\.xlsx' && ! echo "$CMD" | grep -q 'scripts/study.py'; then
  echo "schema-guard: .xlsx is a generated view — produce it via scripts/study.py export" >&2
  exit 2
fi
exit 0
