# Agent Contracts

> Each agent: defined input, output, model, and failure behavior.

---

## Agent 0: SecurityValidatorAgent
- **Input:** `filepath: str`
- **Output:** `{"status": "PASSED"|"BLOCKED", "reason": str}`
- **Model:** `gpt-oss:20b-cloud`
- **On BLOCK:** Orchestrator halts pipeline immediately

## Agent 1: CSVReaderAgent
- **Input:** `filepath: str` (only if security PASSED)
- **Output:** `{"dataframe": pd.DataFrame, "profile": dict}`
- **Model:** `gpt-oss:20b-cloud`
- **On FAIL:** Return error, skip downstream agents

## Agent 2: EDAAnalyzerAgent
- **Input:** `{"dataframe": pd.DataFrame, "profile": dict}`
- **Output:** `{"summary": str, "insights": list, "anomalies": list}`
- **Model:** `gpt-oss:20b-cloud`
- **On FAIL:** Return partial insights, log warning

## Agent 3: ChartGeneratorAgent
- **Input:** `{"dataframe": pd.DataFrame, "insights": list}`
- **Output:** `{"plots": list[filepath], "summary_md": str}`
- **Model:** `gpt-oss:20b-cloud`
- **On FAIL:** Return text summary only
