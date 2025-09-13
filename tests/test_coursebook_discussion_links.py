from pathlib import Path


def test_coursebook_discussion_link_present():
    src = Path("a1sprechen.py").read_text(encoding="utf-8")
    assert "Class Discussion & Notes" in src
    assert "go_discussion_{chapter}" in src
    assert "Discussion for this class can be found at" in src
    assert "#classnotes" in src
