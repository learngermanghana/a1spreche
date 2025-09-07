"""Tests for the writing prompts module."""

import src.schreiben_prompts_module as prompts


def test_get_prompts_for_level_structure():
    """Ensure prompts for each level have the expected structure."""
    for level in ["A1", "A2", "B1", "B2", "C1"]:
        prompts_list = prompts.get_prompts_for_level(level)
        assert isinstance(prompts_list, list)
        assert all(isinstance(p, dict) for p in prompts_list)
        assert all("Thema" in p and "Punkte" in p for p in prompts_list)


def test_each_level_has_minimum_prompts():
    """Each CEFR level should provide a minimum number of prompts."""
    expected_minimums = {"A1": 10, "A2": 10, "B1": 10, "B2": 5, "C1": 5}
    for level, minimum in expected_minimums.items():
        prompts_list = prompts.get_prompts_for_level(level)
        assert len(prompts_list) >= minimum


def test_unknown_level_returns_empty_list():
    """Unknown CEFR levels should result in an empty list."""
    assert prompts.get_prompts_for_level("C2") == []
