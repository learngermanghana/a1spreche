import pytest
from src import resume

class DummyST:
    def __init__(self):
        self.session_state = {}
        self.query_params = {}
        self.info_messages = []
        self.button_calls = []

    def info(self, msg):
        self.info_messages.append(msg)

    def button(self, label, *, on_click=None):
        self.button_calls.append((label, on_click))
        return False

@pytest.fixture
def dummy_st(monkeypatch):
    dummy = DummyST()
    monkeypatch.setattr(resume, "st", dummy)
    return dummy


def test_render_resume_banner_no_progress(dummy_st):
    resume.render_resume_banner()
    assert dummy_st.info_messages == []
    assert dummy_st.button_calls == []


def test_render_resume_banner_with_progress(dummy_st):
    dummy_st.session_state["__last_progress"] = 3
    resume.render_resume_banner()
    assert len(dummy_st.info_messages) == 1
    assert "section 3" in dummy_st.info_messages[0]
    assert len(dummy_st.button_calls) == 1
    label, _ = dummy_st.button_calls[0]
    assert label == "Resume"


def test_resume_navigation_callback(dummy_st):
    dummy_st.session_state["__last_progress"] = 4
    resume.render_resume_banner()
    _, cb = dummy_st.button_calls[0]
    assert cb is not None
    cb()
    assert dummy_st.query_params["section"] == "4"
    assert dummy_st.session_state["needs_rerun"] is True
