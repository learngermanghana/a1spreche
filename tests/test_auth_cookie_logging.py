import logging

from src.auth import SimpleCookieManager, set_student_code_cookie, set_session_token_cookie


class FailingCookieManager(SimpleCookieManager):
    def save(self) -> None:  # pragma: no cover - used for exception path
        raise RuntimeError("boom")


def test_set_student_code_cookie_logs_error(caplog):
    cm = FailingCookieManager()
    with caplog.at_level(logging.ERROR):
        set_student_code_cookie(cm, "abc")
    assert any(
        "Failed to save student code cookie" in record.message
        for record in caplog.records
    )


def test_set_session_token_cookie_logs_error(caplog):
    cm = FailingCookieManager()
    with caplog.at_level(logging.ERROR):
        set_session_token_cookie(cm, "tok")
    assert any(
        "Failed to save session token cookie" in record.message
        for record in caplog.records
    )
