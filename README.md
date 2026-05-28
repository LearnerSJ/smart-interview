# Smart Interview (Claude Code plugin)

Turns a feature brief + customer-interview transcript into a PRD-ready Excel workbook.

## Install

```bash
# clone or copy this folder into your plugins dir
ln -s "$PWD" ~/.claude/plugins/smart-interview
# (or place the folder directly under ~/.claude/plugins/)

# python deps
python3 -m pip install --user openpyxl python-docx python-pptx
```

Restart Claude Code. Then:

```
/smart-interview
```

## Architecture

- **CLAUDE.md** — global rules loaded into context
- **skills/** — orchestrator + 6 sub-skills (reasoning)
- **scripts/workbook.py** — the only thing that writes .xlsx (openpyxl)
- **hooks/** — guardrails (schema lock, QA gate, evidence log)
- **M365 MCP** (already connected in your Claude) — used read-only for calendar + Teams transcripts

## Workflow

1. Intake feature brief
2. Generate interview guide + seed local workbook
3. Pull transcript (M365 SharePoint) OR accept pasted text
4. Extract signals -> score assumptions -> classify
5. Populate workbook (STRONG -> MVP, CONTESTED -> Open Questions, all -> Evidence Log)
6. QA gate
7. (later) push to SharePoint via a write-enabled MCP

Workbook output: `output/<feature_slug>.xlsx`
