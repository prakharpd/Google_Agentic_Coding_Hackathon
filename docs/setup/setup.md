# Setup Guide

## Prerequisites
- Python 3.10+
- Ollama installed and running
- VS Code with Agent Chat panel enabled

## 1. Pull Ollama Models
```bash
ollama pull gpt-oss:20b-cloud   # all agents
ollama pull gpt-oss:120b-cloud  # VS Code vibe coding
```

## 2. Install Dependencies
```bash
pip install google-adk pandas matplotlib plotly seaborn \
            ydata-profiling chardet scipy
```

## 3. VS Code Agent Chat Setup
- Open VS Code → Agent Chat panel
- Set model: `gpt-oss:120b-cloud` (Ollama)
- Open project folder: `business-analyst-agent/`
- Use vibe code prompts from each `docs/agents/*.md`

## 4. Run Order
```bash
python src/agents/orchestrator.py --input data/sample.csv
```

## 4.1 Streamlit Frontend
To run the Streamlit UI for the business analyst agent:
```bash
streamlit run src/app.py
```

## 5. Outputs
- Charts → `outputs/charts/`
- EDA profile → `outputs/profile.html`
- Summary → `outputs/summary.md`
- Audit log → `audit.log`
