"""
Game Strategy Advisor — Streamlit Dashboard
============================================
Imports the three MCP tool functions directly (no HTTP hop needed for local
development), keeping latency and cost to zero on a free trial.

Run:
    streamlit run dashboard.py
"""

from __future__ import annotations

import json
import sys
import os

import streamlit as st
import pandas as pd

# ---------------------------------------------------------------------------
# Allow importing mcp_server from the same directory
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(__file__))

from mcp_server import (
    analyze_match_history,
    detect_opponent_strategy,
    recommend_tactics,
    MOCK_DATA,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Game Strategy Advisor",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — clean tactical look
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Main background */
    .main { background-color: #0d1b2a; color: #e0e0e0; }
    section[data-testid="stSidebar"] { background-color: #1a2b3c; }

    /* Card containers */
    .tactic-card {
        background: #1e3a4a;
        border-left: 4px solid #00c9a7;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 12px;
    }
    .weakness-card {
        background: #3a1e1e;
        border-left: 4px solid #ff6b6b;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
    }
    .summary-box {
        background: #1a3a2a;
        border: 1px solid #00c9a7;
        border-radius: 10px;
        padding: 20px;
        font-size: 1.05rem;
        line-height: 1.7;
    }
    h1 { color: #00c9a7 !important; }
    h2, h3 { color: #a8d8ea !important; }
    .stMetric label { color: #a8d8ea !important; }
    .stMetric [data-testid="stMetricValue"] { color: #00c9a7 !important; font-size: 1.8rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar — team selection
# ---------------------------------------------------------------------------
with st.sidebar:
    st.image(
        "https://img.icons8.com/emoji/96/soccer-ball-emoji.png",
        width=60,
    )
    st.title("⚽ Strategy Advisor")
    st.markdown("---")

    teams = list(MOCK_DATA.keys())
    my_team = st.selectbox("🏆 Your Team", teams, index=0)
    opponent = st.selectbox("🎯 Opponent", [t for t in teams if t != my_team], index=0)

    st.markdown("---")
    analyse_btn = st.button("🔍 Analyse & Recommend", use_container_width=True, type="primary")

    st.markdown("---")
    st.caption("Game Strategy Advisor v1.0\nPowered by FastMCP + IBM Granite")

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("⚽ Multi-Agent Game Strategy Advisor")
st.markdown(
    f"**Your team:** `{my_team}`  &nbsp;&nbsp;|&nbsp;&nbsp;  **Opponent:** `{opponent}`"
)
st.markdown("---")

# ---------------------------------------------------------------------------
# Main logic — only runs after button click
# ---------------------------------------------------------------------------
if not analyse_btn:
    st.info(
        "👈 Select your team and the opponent in the sidebar, "
        "then click **Analyse & Recommend** to generate a scouting report."
    )
    st.stop()

# Spinner while agents work
with st.spinner("Agents working… fetching match data, analysing strategy, computing tactics…"):
    match_data     = json.loads(analyze_match_history(opponent))
    strategy_data  = json.loads(detect_opponent_strategy(opponent))
    tactics_data   = json.loads(recommend_tactics(opponent))

# ---------------------------------------------------------------------------
# Row 1 — KPI metrics
# ---------------------------------------------------------------------------
st.subheader("📊 Opponent Overview")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Preferred Formation",  match_data["preferred_formation"])
c2.metric("Avg Possession",       f"{match_data['avg_possession_pct']}%")
c3.metric("Avg Goals Scored",     match_data["avg_goals_scored"])
c4.metric("Avg Goals Conceded",   match_data["avg_goals_conceded"])
c5.metric("Threat Level",         strategy_data["threat_level"])

st.markdown("---")

# ---------------------------------------------------------------------------
# Row 2 — Match history table + win/loss chart
# ---------------------------------------------------------------------------
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("📅 Last 5 Matches")
    matches_df = pd.DataFrame(match_data["last_5_matches"])
    matches_df.columns = [c.replace("_", " ").title() for c in matches_df.columns]

    def colour_result(val: str) -> str:
        if val.startswith("W"):
            return "background-color: #1a3a2a; color: #00c9a7"
        if val.startswith("L"):
            return "background-color: #3a1e1e; color: #ff6b6b"
        return "background-color: #2a2a1e; color: #f4d03f"

    styled_df = matches_df.style.applymap(colour_result, subset=["Result"])
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

with col_right:
    st.subheader("🏅 Win / Draw / Loss")
    wins   = strategy_data["wins_last_5"]
    losses = strategy_data["losses_last_5"]
    draws  = 5 - wins - losses
    wdl_df = pd.DataFrame(
        {"Result": ["Wins", "Draws", "Losses"], "Count": [wins, draws, losses]}
    ).set_index("Result")
    st.bar_chart(wdl_df, color=["#00c9a7"])

st.markdown("---")

# ---------------------------------------------------------------------------
# Row 3 — Weaknesses detected
# ---------------------------------------------------------------------------
st.subheader("⚠️ Detected Tactical Weaknesses")
weaknesses = strategy_data["detected_weaknesses"]

if weaknesses and weaknesses[0]["id"] != "none":
    wcols = st.columns(min(len(weaknesses), 3))
    for i, w in enumerate(weaknesses):
        with wcols[i % 3]:
            st.markdown(
                f'<div class="weakness-card">🚨 <strong>{w["label"]}</strong></div>',
                unsafe_allow_html=True,
            )
else:
    st.success("✅ No major tactical weaknesses detected. This is a well-balanced opponent!")

st.markdown("---")

# ---------------------------------------------------------------------------
# Row 4 — Recommended formation diagram + key instructions
# ---------------------------------------------------------------------------
col_form, col_inst = st.columns([1, 2])

with col_form:
    st.subheader("🗂️ Recommended Formation")
    formation = tactics_data["recommended_formation"]
    st.markdown(
        f'<div class="tactic-card">'
        f'<h1 style="color:#00c9a7;font-size:3rem;text-align:center">{formation}</h1>'
        f'<p style="text-align:center;color:#a8d8ea">{tactics_data["rationale"]}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ASCII pitch diagram
    formations_ascii: dict[str, list[str]] = {
        "4-3-3":   ["   LW  CF  RW  ", "  LM  CM  RM   ", " LB  CB  CB  RB", "      GK       "],
        "4-2-3-1": ["      CF       ", "  LW  AM  RW   ", "   DM    DM    ", " LB  CB  CB  RB", "      GK       "],
        "3-5-2":   ["   LF      RF  ", " LWB  CM CM RWB", "   CB  CB  CB  ", "      GK       "],
        "4-4-2":   ["  LF       RF  ", " LM  CM  CM  RM", " LB  CB  CB  RB", "      GK       "],
        "5-3-2":   ["   LF      RF  ", "   LM  CM  RM  ", "LWB CB  CB CB RWB","     GK        "],
        "4-5-1":   ["      CF       ", " LM LCM CM RCM RM", " LB  CB  CB  RB", "      GK       "],
    }
    lines = formations_ascii.get(formation, [f"  {formation}  ", "  (custom)  "])
    pitch = "\n".join(lines)

    st.markdown("**Pitch View (Attacking → Defending)**")
    st.code(pitch, language=None)

with col_inst:
    st.subheader("📋 Key Tactical Instructions")
    for i, instruction in enumerate(tactics_data["key_instructions"], 1):
        st.markdown(
            f'<div class="tactic-card">🔹 <strong>Instruction {i}:</strong> {instruction}</div>',
            unsafe_allow_html=True,
        )

st.markdown("---")

# ---------------------------------------------------------------------------
# Row 5 — Insight Explanation Agent (AI summary)
# ---------------------------------------------------------------------------
st.subheader("🤖 Insight Explanation Agent — Scouting Report Summary")
st.markdown(
    f'<div class="summary-box">{tactics_data["summary"]}</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Row 6 — Possession comparison bar chart
# ---------------------------------------------------------------------------
st.markdown("---")
st.subheader("📈 Possession Comparison")

my_stats       = MOCK_DATA[my_team]
opp_avg_poss   = match_data["avg_possession_pct"]
my_avg_poss    = my_stats["avg_possession"]

poss_df = pd.DataFrame(
    {"Team": [my_team, opponent], "Avg Possession %": [my_avg_poss, opp_avg_poss]}
).set_index("Team")
st.bar_chart(poss_df)

# ---------------------------------------------------------------------------
# Row 7 — Raw JSON expander (developer view)
# ---------------------------------------------------------------------------
with st.expander("🔧 Raw Agent Outputs (Developer View)"):
    tab1, tab2, tab3 = st.tabs(["Match Analysis", "Strategy Detection", "Tactics Engine"])
    with tab1:
        st.json(match_data)
    with tab2:
        st.json(strategy_data)
    with tab3:
        st.json(tactics_data)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("---")
st.caption("Game Strategy Advisor · Built with FastMCP + Streamlit · IBM Granite optimised for free-trial usage")
