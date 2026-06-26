# 🤖 AI Business Analyst Agent

> Multi-agent system built with Google ADK + Ollama (gpt-oss:20b-cloud)

## Overview
Accepts CSV input → runs EDA → outputs graphs, plots, patterns, and summaries.

## Agent Pipeline
```
Orchestrator (Google ADK)
├── Agent 0: SecurityValidatorAgent   (prompt injection + data poisoning)
├── Agent 1: CSVReaderAgent           (load + validate CSV)
├── Agent 2: EDAAnalyzerAgent         (stats, nulls, correlations, outliers)
└── Agent 3: ChartGeneratorAgent      (matplotlib / plotly outputs)
```

## Model
- **All Agents:** `gpt-oss:20b-cloud` via Ollama
- **Vibe Coding:** `gpt-oss:120b-cloud` via Ollama (VS Code Agent Chat)

## Quick Start
See [`docs/setup/setup.md`](docs/setup/setup.md)

## Docs
| File | Description |
|------|-------------|
| [architecture.md](docs/architecture.md) | Full system design |
| [security.md](docs/security.md) | Security layer details |
| [agents/](docs/agents/) | Per-agent specs |
