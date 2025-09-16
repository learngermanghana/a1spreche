from pathlib import Path


def test_qna_lesson_link_opens_in_same_tab():
    src = Path("a1sprechen.py").read_text(encoding="utf-8")
    assert "<a href='{course_link}'>View page</a></div>" in src
    assert "target='_blank'>View page</a>" not in src
