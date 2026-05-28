#!/usr/bin/env bash
# Append one audit line per workbook.py invocation. Mark QA state dirty on writes.
set -euo pipefail
INPUT="$(cat)"
CMD="$(echo "$INPUT" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d.get("tool_input",{}).get("command",""))' 2>/dev/null || echo "")"
[ -z "$CMD" ] && exit 0
case "$CMD" in
  *scripts/workbook.py*)
    echo "$(date -u +%FT%TZ) $CMD" >> "$CLAUDE_PROJECT_DIR/hooks/evidence.log"
    case "$CMD" in
      *workbook.py\ seed*|*workbook.py\ write*)
        echo "dirty $(date -u +%FT%TZ)" > "$CLAUDE_PROJECT_DIR/hooks/.qa_state" ;;
    esac
    ;;
esac
exit 0
