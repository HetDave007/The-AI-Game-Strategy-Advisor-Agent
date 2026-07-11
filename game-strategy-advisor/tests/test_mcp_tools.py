"""
Unit Tests — Game Strategy Advisor MCP Tools
=============================================
Tests all three MCP tool functions using the built-in mock data.
No external services, databases, or API keys are required.

Run:
    pytest tests/ -v
    pytest tests/ -v --tb=short   # shorter tracebacks
"""

from __future__ import annotations

import json
import sys
import os
import pytest

# Make sure we can import mcp_server from the parent directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mcp_server import (
    analyze_match_history,
    detect_opponent_strategy,
    recommend_tactics,
    MOCK_DATA,
    FORMATION_MATRIX,
    WEAKNESS_RULES,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ALL_TEAMS = list(MOCK_DATA.keys())


# ---------------------------------------------------------------------------
# analyze_match_history tests
# ---------------------------------------------------------------------------

class TestAnalyzeMatchHistory:

    def test_returns_valid_json_string(self):
        result = analyze_match_history("FC Dynamo")
        data = json.loads(result)          # must not raise
        assert isinstance(data, dict)

    def test_contains_required_keys(self):
        data = json.loads(analyze_match_history("Red Lions"))
        required_keys = {
            "team", "preferred_formation", "avg_possession_pct",
            "defensive_line", "press_intensity", "last_5_matches",
            "avg_goals_scored", "avg_goals_conceded",
        }
        assert required_keys.issubset(data.keys())

    def test_returns_exactly_5_matches(self):
        data = json.loads(analyze_match_history("Blue Hawks"))
        assert len(data["last_5_matches"]) == 5

    def test_each_match_has_required_fields(self):
        data = json.loads(analyze_match_history("Storm City"))
        match_keys = {"date", "opponent", "result", "formation", "goals_scored", "goals_conceded", "possession"}
        for match in data["last_5_matches"]:
            assert match_keys.issubset(match.keys()), f"Match missing keys: {match}"

    def test_avg_goals_scored_is_float(self):
        data = json.loads(analyze_match_history("Phoenix FC"))
        assert isinstance(data["avg_goals_scored"], float)

    def test_avg_goals_conceded_is_float(self):
        data = json.loads(analyze_match_history("Iron Gate"))
        assert isinstance(data["avg_goals_conceded"], float)

    def test_possession_within_valid_range(self):
        data = json.loads(analyze_match_history("FC Dynamo"))
        assert 0 < data["avg_possession_pct"] < 100

    @pytest.mark.parametrize("team", ALL_TEAMS)
    def test_all_teams_return_data(self, team):
        result = analyze_match_history(team)
        data = json.loads(result)
        assert data["team"] == team

    def test_case_insensitive_team_lookup(self):
        result_lower = json.loads(analyze_match_history("fc dynamo"))
        result_upper = json.loads(analyze_match_history("FC DYNAMO"))
        assert result_lower["preferred_formation"] == result_upper["preferred_formation"]

    def test_unknown_team_raises_value_error(self):
        with pytest.raises(ValueError, match="not found"):
            analyze_match_history("Nonexistent FC")


# ---------------------------------------------------------------------------
# detect_opponent_strategy tests
# ---------------------------------------------------------------------------

class TestDetectOpponentStrategy:

    def test_returns_valid_json_string(self):
        result = detect_opponent_strategy("Blue Hawks")
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_contains_required_keys(self):
        data = json.loads(detect_opponent_strategy("Red Lions"))
        required_keys = {
            "team", "threat_level", "wins_last_5",
            "losses_last_5", "detected_weaknesses",
        }
        assert required_keys.issubset(data.keys())

    def test_threat_level_is_valid(self):
        for team in ALL_TEAMS:
            data = json.loads(detect_opponent_strategy(team))
            assert data["threat_level"] in ("High", "Medium", "Low"), \
                f"Unexpected threat level '{data['threat_level']}' for {team}"

    def test_wins_and_losses_sum_to_max_5(self):
        for team in ALL_TEAMS:
            data = json.loads(detect_opponent_strategy(team))
            assert data["wins_last_5"] + data["losses_last_5"] <= 5

    def test_detected_weaknesses_is_list(self):
        data = json.loads(detect_opponent_strategy("Storm City"))
        assert isinstance(data["detected_weaknesses"], list)

    def test_each_weakness_has_id_and_label(self):
        for team in ALL_TEAMS:
            data = json.loads(detect_opponent_strategy(team))
            for w in data["detected_weaknesses"]:
                assert "id" in w, f"Weakness missing 'id' for {team}"
                assert "label" in w, f"Weakness missing 'label' for {team}"

    def test_high_possession_high_press_team_is_counter_vulnerable(self):
        # Blue Hawks: avg_possession=59, defensive_line=high → counter vulnerable
        data = json.loads(detect_opponent_strategy("Blue Hawks"))
        ids = [w["id"] for w in data["detected_weaknesses"]]
        assert "vulnerable_to_counter_attacks" in ids

    def test_unknown_team_raises_value_error(self):
        with pytest.raises(ValueError):
            detect_opponent_strategy("Ghost United")

    @pytest.mark.parametrize("team", ALL_TEAMS)
    def test_all_teams_return_strategy(self, team):
        data = json.loads(detect_opponent_strategy(team))
        assert data["team"] == team


# ---------------------------------------------------------------------------
# recommend_tactics tests
# ---------------------------------------------------------------------------

class TestRecommendTactics:

    def test_returns_valid_json_string(self):
        result = recommend_tactics("Red Lions")
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_contains_required_keys(self):
        data = json.loads(recommend_tactics("Storm City"))
        required_keys = {
            "opponent", "threat_level", "recommended_formation",
            "rationale", "key_instructions", "summary", "detected_weaknesses",
        }
        assert required_keys.issubset(data.keys())

    def test_recommended_formation_is_non_empty_string(self):
        for team in ALL_TEAMS:
            data = json.loads(recommend_tactics(team))
            assert isinstance(data["recommended_formation"], str)
            assert len(data["recommended_formation"]) > 0

    def test_key_instructions_is_non_empty_list(self):
        for team in ALL_TEAMS:
            data = json.loads(recommend_tactics(team))
            assert isinstance(data["key_instructions"], list)
            assert len(data["key_instructions"]) > 0

    def test_summary_mentions_opponent(self):
        team = "Iron Gate"
        data = json.loads(recommend_tactics(team))
        assert team in data["summary"]

    def test_summary_is_non_empty_string(self):
        data = json.loads(recommend_tactics("Phoenix FC"))
        assert isinstance(data["summary"], str)
        assert len(data["summary"]) > 20

    def test_threat_level_matches_strategy(self):
        """recommend_tactics must report the same threat level as detect_opponent_strategy."""
        for team in ALL_TEAMS:
            tactics = json.loads(recommend_tactics(team))
            strategy = json.loads(detect_opponent_strategy(team))
            assert tactics["threat_level"] == strategy["threat_level"]

    def test_formation_matrix_coverage(self):
        """Every known weakness id must have a corresponding formation entry."""
        for weakness_id in WEAKNESS_RULES.keys():
            assert weakness_id in FORMATION_MATRIX, \
                f"FORMATION_MATRIX missing entry for weakness '{weakness_id}'"

    def test_unknown_team_raises_value_error(self):
        with pytest.raises(ValueError):
            recommend_tactics("Invisible Athletic")

    @pytest.mark.parametrize("team", ALL_TEAMS)
    def test_all_teams_return_tactics(self, team):
        data = json.loads(recommend_tactics(team))
        assert data["opponent"] == team


# ---------------------------------------------------------------------------
# Integration test — full pipeline
# ---------------------------------------------------------------------------

class TestFullPipeline:

    def test_pipeline_produces_consistent_outputs(self):
        """
        Runs the full Scout → Analyse → Tactics pipeline for each team
        and asserts internal consistency: threat level and weaknesses
        must be identical across all three agent outputs.
        """
        for team in ALL_TEAMS:
            match   = json.loads(analyze_match_history(team))
            strategy = json.loads(detect_opponent_strategy(team))
            tactics  = json.loads(recommend_tactics(team))

            # All three should agree on the team name
            assert match["team"] == team
            assert strategy["team"] == team
            assert tactics["opponent"] == team

            # Threat level must be consistent between strategy and tactics
            assert strategy["threat_level"] == tactics["threat_level"], \
                f"Threat level mismatch for {team}"

            # Weaknesses in tactics must match those in strategy
            strategy_ids = {w["id"] for w in strategy["detected_weaknesses"]}
            tactics_ids  = {w["id"] for w in tactics["detected_weaknesses"]}
            assert strategy_ids == tactics_ids, \
                f"Weakness ID mismatch for {team}: strategy={strategy_ids}, tactics={tactics_ids}"
