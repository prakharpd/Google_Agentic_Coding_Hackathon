# System Architecture

## Stack
| Layer | Technology |
|-------|-----------|
| Agent Framework | Google ADK (Agent Development Kit) |
| LLM | `gpt-oss:20b-cloud` via Ollama |
| Data | pandas, ydata-profiling |
| Visualization | matplotlib, plotly |
| Security | custom middleware |

## Agent Flow
```
User uploads CSV
        │
        ▼
[SecurityValidatorAgent]  ──BLOCKED──▶ Halt + Log
        │ PASSED
        ▼
[CSVReaderAgent]          ──ERROR──▶ Return schema error
        │ SUCCESS
        ▼
[EDAAnalyzerAgent]        ── stats, nulls, correlations, outliers
        │
        ▼
[ChartGeneratorAgent]     ── outputs PNG/HTML plots
        │
        ▼
[ChartValidatorAgent]     ── validate plots, retry failed charts
        │ PASS
        ▼
[SummaryAgent]            ── generate final markdown summary
        │
        ▼
Final Summary Report (markdown + charts)
```

## Orchestrator Routing (Google ADK)
- Each agent registered as ADK Tool
- Orchestrator uses gpt-oss:20b-cloud for routing decisions
- Sequential pipeline (v1)

## Directory Layout
```
business-analyst-agent/
├── src/
│   ├── agents/
│   │   ├── orchestrator.py
│   │   ├── security_agent.py
│   │   ├── csv_reader_agent.py
│   │   ├── eda_agent.py
│   │   └── chart_agent.py
│   ├── tools/
│   │   ├── file_reader.py
│   │   └── chart_generator.py
│   ├── security/
│   │   └── validator.py
│   └── utils/
│       └── logger.py
├── docs/
│   ├── architecture.md
│   ├── security.md
│   └── agents/
├── tests/
├── outputs/
├── .vscode/
│   └── settings.json
├── requirements.txt
└── README.md
```
