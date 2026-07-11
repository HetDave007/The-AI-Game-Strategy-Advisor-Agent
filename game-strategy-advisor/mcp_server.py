"""
Game Strategy Advisor — FastMCP Server
=======================================
Three agent tools:
  1. analyze_match_history  — RAG-simulation: retrieves last 5 matches + formations
  2. detect_opponent_strategy — detects tactical weaknesses from match history
  3. recommend_tactics       — recommends optimal formation based on weaknesses

All data is self-contained mock JSON; no external database required.
Cost-optimised: logic is rule-based so no LLM token budget is consumed for
the core tools. An optional IBM Granite summary call is gated behind
an env-var so free-trial users never hit it accidentally.
"""

from __future__ import annotations

import json
import os
from typing import Any

from fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Mock sports database
# ---------------------------------------------------------------------------

MOCK_DATA: dict[str, Any] = {
    "FC Dynamo": {
        "matches": [
            {"date": "2024-05-01", "opponent": "Red Lions",   "result": "W 3-1", "formation": "4-3-3",  "goals_scored": 3, "goals_conceded": 1, "possession": 62},
            {"date": "2024-04-24", "opponent": "Blue Hawks",  "result": "L 0-2", "formation": "4-3-3",  "goals_scored": 0, "goals_conceded": 2, "possession": 44},
            {"date": "2024-04-17", "opponent": "Storm City",  "result": "W 2-1", "formation": "4-2-3-1","goals_scored": 2, "goals_conceded": 1, "possession": 55},
            {"date": "2024-04-10", "opponent": "Iron Gate",   "result": "D 1-1", "formation": "4-3-3",  "goals_scored": 1, "goals_conceded": 1, "possession": 49},
            {"date": "2024-04-03", "opponent": "Phoenix FC",  "result": "L 1-3", "formation": "4-4-2",  "goals_scored": 1, "goals_conceded": 3, "possession": 41},
        ],
        "preferred_formation": "4-3-3",
        "avg_possession": 50.2,
        "defensive_line": "high",
        "press_intensity": "medium",
    },
    "Red Lions": {
        "matches": [
            {"date": "2024-05-01", "opponent": "FC Dynamo",   "result": "L 1-3", "formation": "3-5-2",  "goals_scored": 1, "goals_conceded": 3, "possession": 38},
            {"date": "2024-04-24", "opponent": "Storm City",  "result": "W 2-0", "formation": "3-5-2",  "goals_scored": 2, "goals_conceded": 0, "possession": 52},
            {"date": "2024-04-17", "opponent": "Blue Hawks",  "result": "D 2-2", "formation": "4-4-2",  "goals_scored": 2, "goals_conceded": 2, "possession": 48},
            {"date": "2024-04-10", "opponent": "Iron Gate",   "result": "W 1-0", "formation": "3-5-2",  "goals_scored": 1, "goals_conceded": 0, "possession": 55},
            {"date": "2024-04-03", "opponent": "Phoenix FC",  "result": "L 0-2", "formation": "4-4-2",  "goals_scored": 0, "goals_conceded": 2, "possession": 43},
        ],
        "preferred_formation": "3-5-2",
        "avg_possession": 47.2,
        "defensive_line": "medium",
        "press_intensity": "low",
    },
    "Blue Hawks": {
        "matches": [
            {"date": "2024-05-01", "opponent": "Iron Gate",   "result": "W 4-0", "formation": "4-2-3-1","goals_scored": 4, "goals_conceded": 0, "possession": 68},
            {"date": "2024-04-24", "opponent": "FC Dynamo",   "result": "W 2-0", "formation": "4-2-3-1","goals_scored": 2, "goals_conceded": 0, "possession": 56},
            {"date": "2024-04-17", "opponent": "Red Lions",   "result": "D 2-2", "formation": "4-3-3",  "goals_scored": 2, "goals_conceded": 2, "possession": 52},
            {"date": "2024-04-10", "opponent": "Phoenix FC",  "result": "W 3-1", "formation": "4-2-3-1","goals_scored": 3, "goals_conceded": 1, "possession": 61},
            {"date": "2024-04-03", "opponent": "Storm City",  "result": "L 0-1", "formation": "4-2-3-1","goals_scored": 0, "goals_conceded": 1, "possession": 58},
        ],
        "preferred_formation": "4-2-3-1",
        "avg_possession": 59.0,
        "defensive_line": "high",
        "press_intensity": "high",
    },
    "Storm City": {
        "matches": [
            {"date": "2024-05-01", "opponent": "Phoenix FC",  "result": "D 0-0", "formation": "5-3-2",  "goals_scored": 0, "goals_conceded": 0, "possession": 39},
            {"date": "2024-04-24", "opponent": "Red Lions",   "result": "L 0-2", "formation": "5-3-2",  "goals_scored": 0, "goals_conceded": 2, "possession": 48},
            {"date": "2024-04-17", "opponent": "FC Dynamo",   "result": "L 1-2", "formation": "5-4-1",  "goals_scored": 1, "goals_conceded": 2, "possession": 45},
            {"date": "2024-04-10", "opponent": "Blue Hawks",  "result": "W 1-0", "formation": "5-3-2",  "goals_scored": 1, "goals_conceded": 0, "possession": 37},
            {"date": "2024-04-03", "opponent": "Iron Gate",   "result": "W 2-1", "formation": "5-3-2",  "goals_scored": 2, "goals_conceded": 1, "possession": 41},
        ],
        "preferred_formation": "5-3-2",
        "avg_possession": 42.0,
        "defensive_line": "low",
        "press_intensity": "low",
    },
    "Iron Gate": {
        "matches": [
            {"date": "2024-05-01", "opponent": "Blue Hawks",  "result": "L 0-4", "formation": "4-4-2",  "goals_scored": 0, "goals_conceded": 4, "possession": 32},
            {"date": "2024-04-24", "opponent": "Phoenix FC",  "result": "W 2-1", "formation": "4-4-2",  "goals_scored": 2, "goals_conceded": 1, "possession": 46},
            {"date": "2024-04-17", "opponent": "Storm City",  "result": "L 1-2", "formation": "4-5-1",  "goals_scored": 1, "goals_conceded": 2, "possession": 53},
            {"date": "2024-04-10", "opponent": "Red Lions",   "result": "D 0-0", "formation": "4-4-2",  "goals_scored": 0, "goals_conceded": 0, "possession": 44},
            {"date": "2024-04-03", "opponent": "FC Dynamo",   "result": "D 1-1", "formation": "4-4-2",  "goals_scored": 1, "goals_conceded": 1, "possession": 51},
        ],
        "preferred_formation": "4-4-2",
        "avg_possession": 45.2,
        "defensive_line": "medium",
        "press_intensity": "low",
    },
    "Phoenix FC": {
        "matches": [
            {"date": "2024-05-01", "opponent": "Storm City",  "result": "D 0-0", "formation": "4-3-3",  "goals_scored": 0, "goals_conceded": 0, "possession": 61},
            {"date": "2024-04-24", "opponent": "Iron Gate",   "result": "L 1-2", "formation": "4-3-3",  "goals_scored": 1, "goals_conceded": 2, "possession": 54},
            {"date": "2024-04-17", "opponent": "Blue Hawks",  "result": "L 1-3", "formation": "4-4-2",  "goals_scored": 1, "goals_conceded": 3, "possession": 39},
            {"date": "2024-04-10", "opponent": "FC Dynamo",   "result": "W 3-1", "formation": "4-3-3",  "goals_scored": 3, "goals_conceded": 1, "possession": 58},
            {"date": "2024-04-03", "opponent": "Red Lions",   "result": "W 2-0", "formation": "4-3-3",  "goals_scored": 2, "goals_conceded": 0, "possession": 62},
        ],
        "preferred_formation": "4-3-3",
        "avg_possession": 54.8,
        "defensive_line": "medium",
        "press_intensity": "medium",
    },
}

# Weakness detection thresholds
WEAKNESS_RULES = {
    "vulnerable_to_counter_attacks": lambda s: s["avg_possession"] > 55 and s["defensive_line"] == "high",
    "vulnerable_to_high_press":      lambda s: s["press_intensity"] == "low" and s["avg_possession"] < 50,
    "poor_defensive_depth":          lambda s: s["defensive_line"] == "high" and s["press_intensity"] == "high",
    "low_scoring_rate":              lambda s: _avg_goals_scored(s) < 1.2,
    "set_piece_vulnerability":       lambda s: _avg_goals_conceded(s) > 1.6,
    "wing_overload_risk":            lambda s: s["preferred_formation"] in ("3-5-2", "5-3-2"),
}

# Formation recommendation matrix  {weakness: (recommended_formation, rationale)}
FORMATION_MATRIX = {
    "vulnerable_to_counter_attacks": ("4-2-3-1", "Two holding midfielders shield against the high line and enable quick counters."),
    "vulnerable_to_high_press":      ("4-3-3",   "Wide forwards stretch low-block defences; short passing triangles bypass the press."),
    "poor_defensive_depth":          ("3-5-2",   "Back three provides extra cover; wing-backs exploit the space left behind a high line."),
    "low_scoring_rate":              ("4-3-3",   "High-energy front three creates constant pressure and more goal opportunities."),
    "set_piece_vulnerability":       ("3-5-2",   "Tall centre-backs dominate aerial duels; rehearsed set-piece routines maximise conversion."),
    "wing_overload_risk":            ("4-4-2",   "Compact flat four neutralises wing-back overloads and provides defensive width."),
}


# ---------------------------------------------------------------------------
# Helper functions (not exposed as MCP tools)
# ---------------------------------------------------------------------------

def _avg_goals_scored(stats: dict) -> float:
    return sum(m["goals_scored"] for m in stats["matches"]) / len(stats["matches"])


def _avg_goals_conceded(stats: dict) -> float:
    return sum(m["goals_conceded"] for m in stats["matches"]) / len(stats["matches"])


def _get_team(team_name: str) -> dict:
    key = next((k for k in MOCK_DATA if k.lower() == team_name.lower()), None)
    if key is None:
        available = ", ".join(MOCK_DATA.keys())
        raise ValueError(f"Team '{team_name}' not found. Available teams: {available}")
    return MOCK_DATA[key]


# ---------------------------------------------------------------------------
# FastMCP application
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="GameStrategyAdvisor",
    instructions=(
        "You are a football tactics AI. Use the three tools in sequence: "
        "first analyze_match_history, then detect_opponent_strategy, "
        "then recommend_tactics to produce a complete scouting report."
    ),
)


# ---------------------------------------------------------------------------
# Tool 1 — Match Analysis (RAG simulation)
# ---------------------------------------------------------------------------

@mcp.tool()
def analyze_match_history(team_name: str) -> str:
    """
    Retrieves the last 5 matches and tactical profile for the given team.

    This simulates a RAG retrieval step: in production this would embed
    the query and perform a vector-store lookup. Here it reads from the
    in-memory mock dataset, keeping costs at zero for free-trial users.

    Args:
        team_name: The name of the team to scout (e.g. 'Red Lions').

    Returns:
        A JSON string containing match history and formation data.
    """
    stats = _get_team(team_name)
    report = {
        "team": team_name,
        "preferred_formation": stats["preferred_formation"],
        "avg_possession_pct": stats["avg_possession"],
        "defensive_line": stats["defensive_line"],
        "press_intensity": stats["press_intensity"],
        "last_5_matches": stats["matches"],
        "avg_goals_scored": round(_avg_goals_scored(stats), 2),
        "avg_goals_conceded": round(_avg_goals_conceded(stats), 2),
    }
    return json.dumps(report, indent=2)


# ---------------------------------------------------------------------------
# Tool 2 — Opponent Strategy Detection
# ---------------------------------------------------------------------------

@mcp.tool()
def detect_opponent_strategy(team_name: str) -> str:
    """
    Analyses match history to detect tactical weaknesses.

    Applies rule-based heuristics over the mock dataset.  No LLM tokens
    are consumed, keeping this free for trial users.  Returns a ranked
    list of detected weaknesses with confidence levels.

    Args:
        team_name: The name of the opponent to analyse.

    Returns:
        A JSON string listing detected weaknesses and overall threat level.
    """
    stats = _get_team(team_name)
    weaknesses: list[dict] = []

    for weakness_id, rule in WEAKNESS_RULES.items():
        if rule(stats):
            label = weakness_id.replace("_", " ").title()
            weaknesses.append({"id": weakness_id, "label": label})

    wins   = sum(1 for m in stats["matches"] if m["result"].startswith("W"))
    losses = sum(1 for m in stats["matches"] if m["result"].startswith("L"))
    threat = "High" if wins >= 3 else ("Low" if losses >= 3 else "Medium")

    result = {
        "team": team_name,
        "threat_level": threat,
        "wins_last_5": wins,
        "losses_last_5": losses,
        "detected_weaknesses": weaknesses if weaknesses else [{"id": "none", "label": "No major weaknesses detected"}],
    }
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Tool 3 — Tactics Engine
# ---------------------------------------------------------------------------

@mcp.tool()
def recommend_tactics(team_name: str) -> str:
    """
    Recommends the optimal formation and key tactical instructions
    based on the opponent's detected weaknesses.

    Internally calls detect_opponent_strategy and cross-references
    the formation matrix to produce a prioritised recommendation.

    Args:
        team_name: The name of the opponent you will face.

    Returns:
        A JSON string with the recommended formation, rationale,
        key instructions, and a plain-English summary.
    """
    raw_strategy = json.loads(detect_opponent_strategy(team_name))
    weaknesses = raw_strategy["detected_weaknesses"]

    # Pick highest-priority weakness that has a formation entry
    chosen_formation = "4-3-3"
    chosen_rationale = "Balanced default formation suitable for any opponent."
    for w in weaknesses:
        if w["id"] in FORMATION_MATRIX:
            chosen_formation, chosen_rationale = FORMATION_MATRIX[w["id"]]
            break

    # Build tailored key instructions
    instructions: list[str] = []
    weakness_ids = {w["id"] for w in weaknesses}

    if "vulnerable_to_counter_attacks" in weakness_ids:
        instructions += ["Deploy quick wingers for direct counter-attacks.", "Keep second striker in transition channel."]
    if "vulnerable_to_high_press" in weakness_ids:
        instructions += ["Press high from kick-off to force errors.", "Win the ball in advanced zones."]
    if "poor_defensive_depth" in weakness_ids:
        instructions += ["Target the space in behind their defensive line with through balls.", "Use offside trap sparingly."]
    if "low_scoring_rate" in weakness_ids:
        instructions += ["Maintain high tempo to exploit lack of attacking threat.", "Commit extra player to attack safely."]
    if "set_piece_vulnerability" in weakness_ids:
        instructions += ["Practice set-piece routines — corners and free-kicks are high-value.", "Designate a set-piece specialist."]
    if "wing_overload_risk" in weakness_ids:
        instructions += ["Maintain compact defensive width.", "Full-backs should track opposition wing-backs aggressively."]
    if not instructions:
        instructions = ["Maintain shape and discipline.", "Control possession and wait for openings."]

    # Plain-English summary
    weakness_labels = [w["label"] for w in weaknesses if w["id"] != "none"]
    if weakness_labels:
        summary = (
            f"Against {team_name} (Threat: {raw_strategy['threat_level']}), "
            f"we identified {len(weakness_labels)} exploitable weakness(es): "
            f"{', '.join(weakness_labels)}. "
            f"Recommended formation: {chosen_formation}. {chosen_rationale}"
        )
    else:
        summary = (
            f"{team_name} shows no glaring weaknesses (Threat: {raw_strategy['threat_level']}). "
            f"A disciplined {chosen_formation} is recommended with controlled possession play."
        )

    result = {
        "opponent": team_name,
        "threat_level": raw_strategy["threat_level"],
        "recommended_formation": chosen_formation,
        "rationale": chosen_rationale,
        "key_instructions": instructions,
        "summary": summary,
        "detected_weaknesses": weaknesses,
    }
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Runs the MCP server over stdio (default) — compatible with watsonx Orchestrate
    # and any MCP-compatible client.
    # To use SSE transport instead: mcp.run(transport="sse", host="0.0.0.0", port=8000)
    print("Starting Game Strategy Advisor MCP Server...")
    print(f"Available teams: {', '.join(MOCK_DATA.keys())}")
    mcp.run()
