# SummaryAgent

## Role
Create the final markdown summary report using validation output, EDA results, and chart files.

## Model
`gpt-oss:20b-cloud` via Ollama

## Responsibilities
1. Read `outputs/validation_report.md`
2. Read EDA statistics from the EDA agent output
3. Read chart paths from `outputs/charts/`
4. Generate `outputs/summary.md` with dataset overview, EDA findings, chart descriptions, business insights, and data quality notes
5. Log completion to `audit.log`

## Input / Output
- Input: `{"eda_output": dict, "validation_report": str, "chart_paths": list}`
- Output: `{ "status": "COMPLETED", "summary_path": "outputs/summary.md" }`

## Vibe Code Prompt
```
Using gpt-oss:20b-cloud via Ollama and Google ADK, create src/agents/summary_agent.py.
- Read outputs/validation_report.md and EDA stats output
- Inspect chart paths in outputs/charts/
- Generate a polished markdown summary in outputs/summary.md
- Include dataset overview, column-level EDA findings, chart descriptions, top 3 business insights, and data quality notes
- Log completion to audit.log
```