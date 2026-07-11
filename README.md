# The-AI-Game-Strategy-Advisor-Agent
An AI-powered gaming assistant that analyzes gameplay data, tracks real-time match state, and provides dynamic strategic recommendations to optimize player decision-making.
# ⚽ Game Strategy Advisor

> A **multi-agent AI system** that scouts opponents, detects tactical weaknesses, and delivers real-time formation recommendations — visualised on an interactive Streamlit dashboard.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![FastMCP](https://img.shields.io/badge/FastMCP-2.0%2B-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?logo=streamlit&logoColor=white)
![IBM Granite](https://img.shields.io/badge/IBM%20Granite-watsonx-0530AD?logo=ibm&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Dashboard](#dashboard)
- [Multi-Agent Workflow](#multi-agent-workflow)
- [MCP Tools Reference](#mcp-tools-reference)
- [Available Teams (Mock Data)](#available-teams-mock-data)
- [Connecting to watsonx Orchestrate](#connecting-to-watsonx-orchestrate)
- [Langflow RAG Pipeline](#langflow-rag-pipeline)
- [Running Tests](#running-tests)
- [Cost Optimisation](#cost-optimisation)
- [Extending the System](#extending-the-system)
- [Environment Variables](#environment-variables)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

Game Strategy Advisor is a football (soccer) tactics intelligence platform built on top of the **Model Context Protocol (MCP)**. Three specialised AI agents collaborate in sequence to produce a complete pre-match scouting report:

1. **Scout Agent** — retrieves the last 5 matches and full tactical profile of the opponent.
2. **Analyst Agent** — applies rule-based heuristics to detect exploitable weaknesses (counter-attack vulnerability, high-press susceptibility, set-piece risk, etc.).
3. **Tactics Engine** — recommends the optimal formation and generates per-weakness tactical instructions.

All tools are **rule-based by default** (zero LLM token cost), making the system perfectly suited for IBM watsonx **free-trial** accounts. Optional IBM Granite summaries can be enabled via a single environment variable.

---

## Features

- 🔍 **Match History Analysis** — last 5 matches with formation, possession, goals scored/conceded
- 🧠 **Automated Weakness Detection** — 6 rule-based heuristics (counter-attack, high press, wing overload, set pieces, defensive depth, scoring rate)
- 🗂️ **Formation Recommendation Engine** — formation matrix cross-referenced against detected weaknesses
- 📋 **Tactical Instructions** — per-weakness coaching instructions generated automatically
- 📊 **Interactive Streamlit Dashboard** — KPI metrics, colour-coded match table, possession chart, ASCII pitch diagram
- 🤖 **watsonx Orchestrate Integration** — ready-to-import multi-agent YAML definition
- 🌊 **Langflow RAG Pipeline** — visual pipeline guide for IBM Langflow
- ✅ **Full Unit Test Suite** — 30+ tests covering all three MCP tools and the full pipeline
- 💸 **Zero mandatory cloud cost** — all core functionality runs entirely offline

---

## Project Structure

```
game-strategy-advisor/
├── mcp_server.py          ← FastMCP server — 3 agent tools + mock data
├── dashboard.py           ← Streamlit visual dashboard
├── watsonx-agent.yaml     ← Multi-agent definition for watsonx Orchestrate
├── LANGFLOW_GUIDE.md      ← Step-by-step guide to wire into Langflow
├── requirements.txt       ← Python dependencies
└── tests/
    └── test_mcp_tools.py  ← Unit tests for all MCP tools
```

---

## Quick Start

### Prerequisites

- Python **3.10 or higher**
- `pip` package manager

### 1 · Clone the repository

```bash
git clone https://github.com/your-username/game-strategy-advisor.git
cd game-strategy-advisor
```

### 2 · Create and activate a virtual environment

```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3 · Install dependencies

```bash
pip install -r requirements.txt
```

> **Free-trial tip:** `langflow` and `ibm-watsonx-ai` are optional. The MCP server and Streamlit dashboard run with zero cloud dependencies using the built-in mock dataset.

### 4 · Start the MCP server

```bash
python mcp_server.py
```

Expected output:
```
Starting Game Strategy Advisor MCP Server...
Available teams: FC Dynamo, Red Lions, Blue Hawks, Storm City, Iron Gate, Phoenix FC
```

The server runs over **stdio** by default (MCP standard). To expose it over HTTP/SSE for remote clients, change the last line of `mcp_server.py`:

```python
# Default (stdio):
mcp.run()

# Remote / SSE transport:
mcp.run(transport="sse", host="0.0.0.0", port=8000)
```

---

## Dashboard

Launch the Streamlit dashboard in a **second terminal** (venv activated):

```bash
streamlit run dashboard.py
```

Open **http://localhost:8501** in your browser.

### How to use

| Step | Action |
|------|--------|
| 1 | Select **Your Team** from the sidebar dropdown |
| 2 | Select the **Opponent** you want to scout |
| 3 | Click **🔍 Analyse & Recommend** |

### Dashboard sections

| Section | Description |
|---------|-------------|
| 📊 Opponent Overview | KPI metrics: formation, possession %, avg goals, threat level |
| 📅 Last 5 Matches | Colour-coded W/D/L match history table |
| 🏅 Win / Draw / Loss | Bar chart of the last 5 results |
| ⚠️ Detected Weaknesses | Cards showing all exploitable tactical weaknesses |
| 🗂️ Recommended Formation | ASCII pitch diagram with the optimal formation |
| 📋 Key Instructions | Per-weakness tactical coaching instructions |
| 🤖 Scouting Report | AI-generated plain-English coaching summary |
| 📈 Possession Comparison | Your team vs opponent possession bar chart |
| 🔧 Raw Agent Outputs | JSON developer view for all three agent responses |

---

## Multi-Agent Workflow

```
User (coach) types opponent name
         │
         ▼
┌─────────────────────┐
│   Scout Agent       │  analyze_match_history(opponent)
│   (IBM Granite)     │  → retrieves last 5 matches + formation profile
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   Analyst Agent     │  detect_opponent_strategy(opponent)
│   (IBM Granite)     │  → detects weaknesses & threat level
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Tactics Engine     │  recommend_tactics(opponent)
│  Agent (IBM Granite)│  → recommends formation + instructions + summary
└────────┬────────────┘
         │
         ▼
   Dashboard / Chat Output
```

All agents share the same lightweight `ibm/granite-3-8b-instruct` model and are coordinated by a top-level **Strategy Orchestrator** defined in [`watsonx-agent.yaml`](watsonx-agent.yaml).

---

## MCP Tools Reference

### `analyze_match_history(team_name: str) → str`

Retrieves the tactical profile and last 5 match results for a team.

**Returns (JSON):**
```json
{
  "team": "Red Lions",
  "preferred_formation": "3-5-2",
  "avg_possession_pct": 47.2,
  "defensive_line": "medium",
  "press_intensity": "low",
  "last_5_matches": [ ... ],
  "avg_goals_scored": 1.2,
  "avg_goals_conceded": 1.0
}
```

---

### `detect_opponent_strategy(team_name: str) → str`

Applies 6 rule-based heuristics to detect exploitable weaknesses.

| Weakness ID | Trigger Condition |
|-------------|-------------------|
| `vulnerable_to_counter_attacks` | Avg possession > 55% **and** high defensive line |
| `vulnerable_to_high_press` | Low press intensity **and** avg possession < 50% |
| `poor_defensive_depth` | High defensive line **and** high press intensity |
| `low_scoring_rate` | Avg goals scored < 1.2 per game |
| `set_piece_vulnerability` | Avg goals conceded > 1.6 per game |
| `wing_overload_risk` | Preferred formation is `3-5-2` or `5-3-2` |

**Returns (JSON):**
```json
{
  "team": "Blue Hawks",
  "threat_level": "High",
  "wins_last_5": 4,
  "losses_last_5": 1,
  "detected_weaknesses": [
    { "id": "vulnerable_to_counter_attacks", "label": "Vulnerable To Counter Attacks" }
  ]
}
```

---

### `recommend_tactics(team_name: str) → str`

Cross-references detected weaknesses against the formation matrix to produce a complete game plan.

**Returns (JSON):**
```json
{
  "opponent": "Blue Hawks",
  "threat_level": "High",
  "recommended_formation": "4-2-3-1",
  "rationale": "Two holding midfielders shield against the high line and enable quick counters.",
  "key_instructions": [ "Deploy quick wingers for direct counter-attacks.", ... ],
  "summary": "Against Blue Hawks (Threat: High), we identified 1 exploitable weakness...",
  "detected_weaknesses": [ ... ]
}
```

---

## Available Teams (Mock Data)

| Team | Preferred Formation | Avg Possession | Defensive Line | Press Intensity | Style |
|------|---------------------|---------------|----------------|-----------------|-------|
| FC Dynamo | 4-3-3 | 50.2% | High | Medium | Balanced |
| Red Lions | 3-5-2 | 47.2% | Medium | Low | Counter |
| Blue Hawks | 4-2-3-1 | 59.0% | High | High | Possession |
| Storm City | 5-3-2 | 42.0% | Low | Low | Defensive |
| Iron Gate | 4-4-2 | 45.2% | Medium | Low | Compact |
| Phoenix FC | 4-3-3 | 54.8% | Medium | Medium | Attacking |

Team names are **case-insensitive** (e.g. `"fc dynamo"` and `"FC DYNAMO"` both work).

---

## Connecting to watsonx Orchestrate

1. **Install the CLI:**
   ```bash
   pip install ibm-watsonx-orchestrate
   ```

2. **Set environment variables:**
   ```bash
   export WATSONX_API_KEY=your_key_here
   export WATSONX_PROJECT_ID=your_project_id
   export WATSONX_URL=https://us-south.ml.cloud.ibm.com
   ```

3. **Login and import the agent definition:**
   ```bash
   orchestrate login --apikey $WATSONX_API_KEY --instance-url $WATSONX_URL
   orchestrate agents import -f watsonx-agent.yaml
   ```

4. **Start the MCP server** (must be running when Orchestrate calls it):
   ```bash
   python mcp_server.py
   ```

The `watsonx-agent.yaml` defines four agents: **Scout Agent**, **Analyst Agent**, **Tactics Engine Agent**, and a **Strategy Orchestrator** that runs them sequentially.

---

## Langflow RAG Pipeline

See [`LANGFLOW_GUIDE.md`](LANGFLOW_GUIDE.md) for a complete step-by-step guide to wiring the three MCP tools into an IBM Langflow visual canvas, including:

- Chat Input → Prompt Template → Python Function components
- IBM Granite LLM component configuration
- Optional Chroma DB / FAISS vector store upgrade for true RAG
- Troubleshooting table for common issues

```bash
# Start Langflow locally
python -m langflow run
# Opens at http://localhost:7860
```

---

## Running Tests

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run with shorter tracebacks
pytest tests/ -v --tb=short
```

The test suite covers:

| Test Class | Coverage |
|------------|----------|
| `TestAnalyzeMatchHistory` | JSON structure, field types, all 6 teams, case-insensitive lookup, unknown team error |
| `TestDetectOpponentStrategy` | Threat levels, weakness detection correctness, wins/losses bounds |
| `TestRecommendTactics` | Formation validity, instructions non-empty, summary content, threat level consistency |
| `TestFullPipeline` | End-to-end Scout → Analyse → Tactics consistency for all 6 teams |

---

## Cost Optimisation

All core tools are rule-based Python — no LLM calls are made unless explicitly configured.

| Component | Cost | Notes |
|-----------|------|-------|
| `analyze_match_history` | **$0** | Pure Python, no LLM call |
| `detect_opponent_strategy` | **$0** | Rule-based heuristics only |
| `recommend_tactics` | **$0** | Rule-based formation matrix |
| Streamlit dashboard | **$0** | Runs locally, no cloud required |
| IBM Granite (optional) | ~$0 | `granite-3-8b-instruct` — lightest free-tier model |
| Langflow | **$0** | Runs locally |
| Embeddings (optional RAG) | ~$0 | `slate-125m-english-rtrvr` — 125M params |

---

## Extending the System

### Add a real team

Add an entry to `MOCK_DATA` in [`mcp_server.py`](mcp_server.py) following the existing schema:

```python
"My New Team": {
    "matches": [ ... ],          # list of 5 match dicts
    "preferred_formation": "4-3-3",
    "avg_possession": 52.0,
    "defensive_line": "medium",  # "high" | "medium" | "low"
    "press_intensity": "medium", # "high" | "medium" | "low"
}
```

### Add a new weakness rule

Add a lambda to `WEAKNESS_RULES` and a corresponding entry in `FORMATION_MATRIX`:

```python
WEAKNESS_RULES["new_weakness_id"] = lambda s: s["avg_possession"] < 35

FORMATION_MATRIX["new_weakness_id"] = (
    "4-3-3",
    "High-energy front three exploits low-possession teams."
)
```

### Enable IBM Granite summaries

Set `WATSONX_API_KEY` before launching the dashboard. Extend `dashboard.py` to call `ibm-watsonx-ai` for richer natural-language summaries when the key is present.

### Upgrade to real RAG

Replace the mock data lookup in `analyze_match_history` with a **Chroma** or **FAISS** vector store populated with real match report documents, using IBM's `slate-125m-english-rtrvr` embedding model.

---

## Environment Variables

Create a `.env` file in the project root (**never commit this file**):

```bash
WATSONX_API_KEY=your_api_key_here
WATSONX_PROJECT_ID=your_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com
```

Load in Python:

```python
from dotenv import load_dotenv
load_dotenv()
```

---

## Contributing

Contributions are welcome! To get started:

1. **Fork** the repository and create a feature branch:
   ```bash
   git checkout -b feature/my-new-feature
   ```
2. Make your changes and ensure all tests pass:
   ```bash
   pytest tests/ -v
   ```
3. **Commit** with a clear message and open a **Pull Request**.

Please keep PRs focused — one feature or fix per PR. Add tests for any new MCP tools or weakness rules.

---

## License

This project is licensed under the **MIT License** — free to use, modify, and distribute.

---

<div align="center">
  <sub>Built with ⚽ FastMCP · Streamlit · IBM Granite on watsonx</sub>
</div>

