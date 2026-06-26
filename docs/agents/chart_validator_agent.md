# ChartValidatorAgent

## Role
Validate generated chart visuals against the original CSV data and enforce quality checks.

## Model
`gpt-oss:20b-cloud` via Ollama (reviewer feedback only)

## Responsibilities
1. Load generated PNG charts and metadata
2. Validate x-axis range, bin count, file size, KDE peak, and skewness direction
3. Generate LLM feedback for failed charts
4. Retry failed chart generation up to 3 times
5. Halt pipeline if chart validation still fails

## Input / Output
- Input: `{"csv_path": str, "eda": dict, "df": pandas.DataFrame}`
- Output: `{ "status": "PASS"|"FAIL", "feedback": dict }

## Vibe Code Prompt
```
Using gpt-oss:20b-cloud via Ollama and Google ADK, create src/agents/chart_validator_agent.py.
- Build a pure-python validation layer that reads CSV data and chart PNG metadata
- Check x-axis bounds, Sturges rule bin count, file size, KDE peak location, and skewness direction
- Use a second LLM pass to turn failures into clear ChartAgent fix instructions
- Retry failed charts up to 3 times; if still failing, save outputs/validation_failed.md
- Log every attempt to audit.log and write outputs/validation_report.md
```