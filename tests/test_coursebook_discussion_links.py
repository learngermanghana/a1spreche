from src.discussion_board import (
    CLASS_DISCUSSION_LABEL,
    CLASS_DISCUSSION_LINK_TMPL,
    CLASS_DISCUSSION_PROMPT,
    CLASS_DISCUSSION_ANCHOR,
)


def test_coursebook_discussion_link_present():
    assert CLASS_DISCUSSION_LABEL == "Class Discussion & Notes"
    assert CLASS_DISCUSSION_LINK_TMPL == "go_discussion_{chapter}"
    assert "Discussion for this class" in CLASS_DISCUSSION_PROMPT
    assert CLASS_DISCUSSION_ANCHOR == "#classnotes"
