from pathlib import Path

def test_coursebook_navigation_links_present():
    src = Path("a1sprechen.py").read_text(encoding="utf-8")
    assert "_go_coursebook_lesson" in src
    assert "key=f\"go_day_{day}\"" in src
    assert "key=f\"go_day_{day}_next\"" in src
