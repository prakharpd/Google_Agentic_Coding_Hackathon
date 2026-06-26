# ChartGeneratorAgent

## Role
Auto-generate charts based on EDA output.

## Model
`gpt-oss:20b-cloud` via Ollama (selects chart types)

## Chart Types
| Data Type | Chart |
|-----------|-------|
| Numeric distribution | Histogram + KDE |
| Outliers | Boxplot |
| Correlations | Heatmap (seaborn) |
| Trends | Line chart (plotly) |
| Categorical | Bar chart |

## Input / Output
- Input: EDA dict from EDAAnalyzerAgent
- Output: `{ "charts": ["outputs/charts/hist_col1.png", ...] }`

## Vibe Code Prompt
```
Using gpt-oss:20b-cloud via Ollama and Google ADK, create src/agents/chart_agent.py.
- Use gpt-oss:20b-cloud to decide chart types per column from EDA dict
- Generate: histogram+KDE, boxplot, heatmap, bar/line charts
- Use matplotlib + plotly; save all to outputs/charts/
- Return dict with chart paths list
```
