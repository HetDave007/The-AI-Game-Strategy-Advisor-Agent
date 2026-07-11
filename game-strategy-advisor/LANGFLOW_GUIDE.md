# Langflow RAG Pipeline — Integration Guide

## Overview

This guide explains how to wire the **Game Strategy Advisor** Python endpoints
into the **IBM Langflow** visual builder to create a fully visual RAG pipeline.
No paid subscription is required for local testing — Langflow runs entirely on
your machine and the data stays in the mock JSON dataset.

---

## Prerequisites

| Requirement | Version | Install command |
|---|---|---|
| Python | ≥ 3.10 | — |
| Langflow | ≥ 1.0 | `pip install langflow` |
| FastMCP | ≥ 2.0 | `pip install fastmcp` |

Start Langflow:

```bash
python -m langflow run
# Opens at http://localhost:7860
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  Langflow Canvas                    │
│                                                     │
│  [Chat Input]                                       │
│       │                                             │
│       ▼                                             │
│  [Prompt Template]  ◄──── "Scout {opponent_name}"  │
│       │                                             │
│       ▼                                             │
│  [Python Function: analyze_match_history]           │
│       │                                             │
│       ▼                                             │
│  [Python Function: detect_opponent_strategy]        │
│       │                                             │
│       ▼                                             │
│  [Python Function: recommend_tactics]               │
│       │                                             │
│       ▼                                             │
│  [IBM Granite LLM Component]  ◄── summarise report │
│       │                                             │
│       ▼                                             │
│  [Chat Output]                                      │
└─────────────────────────────────────────────────────┘
```

---

## Step-by-Step Wiring

### 1 · Create a New Flow

1. Open `http://localhost:7860` in your browser.
2. Click **New Flow → Blank Flow**.
3. Name it `Game Strategy RAG Pipeline`.

---

### 2 · Add a Chat Input Component

1. In the left panel, search **"Chat Input"** and drag it onto the canvas.
2. This becomes the entry point — the coach types an opponent name here
   (e.g. `"Red Lions"`).

---

### 3 · Add a Prompt Template Component

1. Drag a **"Prompt"** component onto the canvas.
2. Set the template to:
   ```
   You are a football tactics AI. The opponent team is: {opponent_name}.
   Retrieve their match history, detect weaknesses, and recommend tactics.
   ```
3. Connect **Chat Input → Prompt** (map `text` output → `opponent_name` input).

---

### 4 · Add Python Function Components (one per tool)

For each of the three MCP tools, add a **"Python Function"** component:

#### Component A — Match Analysis

- **Function Name:** `analyze_match_history`
- **Code:**

```python
import sys, os
sys.path.insert(0, "/absolute/path/to/game-strategy-advisor")
from mcp_server import analyze_match_history

def run(opponent_name: str) -> str:
    return analyze_match_history(opponent_name)
```

- **Input:** `opponent_name` (string)
- **Output:** `match_json` (string)

#### Component B — Strategy Detection

- **Function Name:** `detect_opponent_strategy`
- **Code:**

```python
import sys, os
sys.path.insert(0, "/absolute/path/to/game-strategy-advisor")
from mcp_server import detect_opponent_strategy

def run(opponent_name: str) -> str:
    return detect_opponent_strategy(opponent_name)
```

- **Input:** `opponent_name` (string, connect from Prompt output)
- **Output:** `strategy_json` (string)

#### Component C — Tactics Engine

- **Function Name:** `recommend_tactics`
- **Code:**

```python
import sys, os
sys.path.insert(0, "/absolute/path/to/game-strategy-advisor")
from mcp_server import recommend_tactics

def run(opponent_name: str) -> str:
    return recommend_tactics(opponent_name)
```

- **Input:** `opponent_name` (string, connect from Prompt output)
- **Output:** `tactics_json` (string)

---

### 5 · Add the IBM Granite LLM Component

1. Drag an **"IBM watsonx"** LLM component onto the canvas.
2. Configure it:

| Field | Value |
|---|---|
| Model | `ibm/granite-3-8b-instruct` |
| API Key | Your `WATSONX_API_KEY` env var |
| Project ID | Your `WATSONX_PROJECT_ID` env var |
| Max Tokens | `512` (cost-efficient for free tier) |
| Temperature | `0.2` |

3. Set the **System Prompt:**
   ```
   You are a football coach AI. Given the JSON outputs from three analysis
   tools, produce a concise, motivational game plan in plain English.
   Format: Formation | Key Instructions (numbered) | Coaching Summary.
   ```

4. **Connect the three Python function outputs** into the LLM component's
   `context` or `human_message` input as a combined string:
   ```
   Match Data: {match_json}
   Strategy: {strategy_json}
   Tactics: {tactics_json}
   ```
   Use a **"Prompt"** component to combine the three JSON strings before
   feeding them to the LLM.

---

### 6 · Add Chat Output

1. Drag a **"Chat Output"** component onto the canvas.
2. Connect **IBM Granite LLM → Chat Output**.

---

### 7 · Wire the Full Flow

Final connection map:

```
Chat Input
    └──► Prompt Template (extract opponent_name)
              ├──► Python: analyze_match_history  ──┐
              ├──► Python: detect_opponent_strategy ─┼──► Combine Prompt
              └──► Python: recommend_tactics      ──┘         │
                                                               ▼
                                                    IBM Granite LLM
                                                               │
                                                               ▼
                                                        Chat Output
```

---

### 8 · Test the Flow

1. Click the **▶ Run** button (bottom right of canvas).
2. In the **Chat Input** box type: `Red Lions`
3. Expected output: A complete game plan with formation, instructions,
   and a coaching summary generated by IBM Granite.

---

## RAG Enhancement (Optional — No Extra Cost)

To add true vector retrieval (replacing the mock data lookup):

1. Add a **"Chroma DB"** or **"FAISS"** vector store component.
2. Add an **"IBM watsonx Embeddings"** component
   (model: `ibm/slate-125m-english-rtrvr` — free tier).
3. Ingest historical match reports as text documents into the vector store.
4. Replace the `analyze_match_history` Python function with a
   **retrieval chain**: query → embed → vector search → return top-k chunks.

This keeps embedding costs near-zero on a free trial because
`slate-125m-english-rtrvr` is a lightweight 125M parameter model.

---

## Environment Variables

Create a `.env` file in the project root (never commit this file):

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

## Troubleshooting

| Issue | Fix |
|---|---|
| `ModuleNotFoundError: mcp_server` | Set absolute path in `sys.path.insert()` |
| LLM component shows auth error | Verify `WATSONX_API_KEY` and `WATSONX_PROJECT_ID` |
| Langflow port conflict | Use `python -m langflow run --port 7861` |
| IBM Granite model not found | Ensure your instance region matches `WATSONX_URL` |
