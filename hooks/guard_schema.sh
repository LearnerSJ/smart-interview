#!/usr/bin/env bash
# Block any .xlsx mutation that doesn't go through scripts/workbook.py.
set -euo pipefail
INPUT="$(cat)"
CMD="$(echo "$INPUT" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d.get("tool_input",{}).get("command",""))' 2>/dev/null || echo "")"
if echo "$CMD" | grep -Eq '\.xlsx' && ! echo "$CMD" | grep -q 'scripts/workbook.py'; then
  echo "schema-guard: .xlsx writes must go through scripts/workbook.py" >&2
  exit 2
fi
exit 0
