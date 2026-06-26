# EDAAnalyzerAgent

## Role
Full exploratory data analysis and pattern extraction.

## Model
`gpt-oss:20b-cloud` via Ollama

## Responsibilities
1. Descriptive stats (mean, median, std, skewness, kurtosis)
2. Null/missing value analysis
3. Correlation matrix
4. Outlier detection (IQR method)
5. LLM-generated natural language summary

## Input / Output
- Input: pandas DataFrame
- Output: `{ "stats": {}, "nulls": {}, "correlations": {}, "outliers": {}, "llm_summary": "string" }`

## Vibe Code Prompt
```
Using gpt-oss:20b-cloud via Ollama and Google ADK, create src/agents/eda_agent.py.
- Compute: descriptive stats, null analysis, correlation matrix, IQR outlier detection
- Call gpt-oss:20b-cloud via Ollama for natural language EDA summary
- Use only pandas and scipy
- Return structured dict as above
```
