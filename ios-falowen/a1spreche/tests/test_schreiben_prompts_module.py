"""Tests for the writing prompts module."""

import src.schreiben_prompts_module as prompts


def test_get_prompts_for_level_structure():
    """Ensure A1 prompts have expected structure."""
    prompts_list = prompts.get_prompts_for_level("A1")
    assert isinstance(prompts_list, list)
    assert all(isinstance(p, dict) for p in prompts_list)
    assert all("Thema" in p and "Punkte" in p for p in prompts_list)


def test_each_level_has_at_least_ten_prompts():
    """All defined CEFR levels should provide at least ten prompts."""
    for level in ["A1", "A2", "B1"]:
        prompts_list = prompts.get_prompts_for_level(level)
        assert len(prompts_list) >= 10


def test_unknown_level_returns_empty_list():
    """Unknown CEFR levels should result in an empty list."""
    assert prompts.get_prompts_for_level("C1") == []
