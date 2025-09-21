import src.ui_components as ui


class DummyStreamlit:
    def __init__(self):
        self.markdowns = []
        self.button_calls = []
        self.session_state = {}
        self.next_button_result = False

    def markdown(self, text, **kwargs):  # pragma: no cover - trivial
        self.markdowns.append((text, kwargs))

    def button(self, label, **kwargs):  # pragma: no cover - trivial
        self.button_calls.append((label, kwargs))
        return self.next_button_result


def test_assignment_reminder_no_cta_by_default(monkeypatch):
    st = DummyStreamlit()
    monkeypatch.setattr(ui, "st", st)

    ui.render_assignment_reminder()

    assert st.button_calls == []


def test_assignment_reminder_cta_sets_session_state(monkeypatch):
    st = DummyStreamlit()
    st.next_button_result = True
    monkeypatch.setattr(ui, "st", st)

    ui.render_assignment_reminder(show_grammar_cta=True)

    assert st.button_calls == [
        ("Ask a grammar question", {"use_container_width": True})
    ]
    assert st.session_state == {
        "nav_sel": "Chat • Grammar • Exams",
        "main_tab_select": "Chat • Grammar • Exams",
        "need_rerun": True,
    }
