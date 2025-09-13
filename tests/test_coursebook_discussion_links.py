from pathlib import Path


def test_coursebook_discussion_link_present():
    src = Path("a1sprechen.py").read_text(encoding="utf-8")
    assert "Class Discussion & Notes" in src
    assert "go_discussion_{info['chapter']}" in src
    assert "Check the group discussion for this chapter and class notes." in src
