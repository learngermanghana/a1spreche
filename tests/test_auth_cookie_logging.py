import logging

from src.auth import SimpleCookieManager, set_student_code_cookie, set_session_token_cookie


class FailingCookieManager(SimpleCookieManager):
    def save(self) -> None:  # pragma: no cover - ensures save isn't called
        raise RuntimeError("boom")


def test_set_student_code_cookie_no_error_when_save_not_called(caplog):
    cm = FailingCookieManager()
    with caplog.at_level(logging.ERROR):
        set_student_code_cookie(cm, "abc")
    assert cm.get("student_code") == "abc"
    assert not caplog.records


def test_set_session_token_cookie_no_error_when_save_not_called(caplog):
    cm = FailingCookieManager()
    with caplog.at_level(logging.ERROR):
        set_session_token_cookie(cm, "tok")
    assert cm.get("session_token") == "tok"
    assert not caplog.records
