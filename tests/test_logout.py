import logging

import pytest

from src import logout


class DummySt:
    def __init__(self):
        self.session_state = {
            "session_token": "token-123",
            "student_code": "STUDENT42",
            "classroom_comment_draft_week1": "Remember to review.",
            "q_text": "New question draft",
            "q_edit_text_post123": "Editing existing question",
            "c_edit_text_post123_comment456": "Editing a reply",
        }
        self.query_params = {}
        self.messages = []

    def success(self, message):
        self.messages.append(message)


@pytest.fixture(autouse=True)
def clear_log_handlers():
    # Ensure logger errors do not propagate between tests
    logger = logging.getLogger()
    handlers = list(logger.handlers)
    for handler in handlers:
        logger.removeHandler(handler)
    try:
        yield
    finally:
        for handler in handlers:
            logger.addHandler(handler)


def test_do_logout_persists_classroom_comment_drafts(monkeypatch):
    saved = []

    def fake_save(code, key, value):
        saved.append((code, key, value))

    monkeypatch.setattr(logout, "save_draft_to_db", fake_save)

    st_module = DummySt()

    logout.do_logout(
        st_module=st_module,
        destroy_token=lambda token: None,
        logger=logging,
    )

    assert (
        "STUDENT42",
        "classroom_comment_draft_week1",
        "Remember to review.",
    ) in saved
    assert ("STUDENT42", "q_text", "New question draft") in saved
    assert ("STUDENT42", "q_edit_text_post123", "Editing existing question") in saved
    assert (
        "STUDENT42",
        "c_edit_text_post123_comment456",
        "Editing a reply",
    ) in saved
