#!/usr/bin/env bash
# Append one audit line per study.py invocation. Mark QA state dirty on data writes.
set -euo pipefail
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT="$(cat)"
CMD="$(echo "$INPUT" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d.get("tool_input",{}).get("command",""))' 2>/dev/null || echo "")"
[ -z "$CMD" ] && exit 0
case "$CMD" in
  *scripts/study.py*)
    echo "$(date -u +%FT%TZ) $CMD" >> "$HOOK_DIR/evidence.log"
    case "$CMD" in
      *study.py\ create-study*|*study.py\ add-interview*|*study.py\ add-assumption*)
        echo "dirty $(date -u +%FT%TZ)" > "$HOOK_DIR/.qa_state" ;;
    esac
    ;;
esac
exit 0
