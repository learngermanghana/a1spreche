import src.ui_components as ui


class DummyStreamlit:
    def __init__(self):
        self.markdowns = []
        self.button_calls = []
        self.session_state = {}

    def markdown(self, text, **kwargs):  # pragma: no cover - trivial
        self.markdowns.append((text, kwargs))


def test_assignment_reminder_renders_notice(monkeypatch):
    st = DummyStreamlit()
    monkeypatch.setattr(ui, "st", st)

    ui.render_assignment_reminder()

    assert len(st.markdowns) == 1
    text, kwargs = st.markdowns[0]
    assert "Your Assignment" in text
    assert kwargs.get("unsafe_allow_html") is True


def test_assignment_reminder_does_not_render_cta(monkeypatch):
    st = DummyStreamlit()
    monkeypatch.setattr(ui, "st", st)

    ui.render_assignment_reminder()

    assert st.button_calls == []
    assert st.session_state == {}
