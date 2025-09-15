import src.ui_components as ui


class ST:
    def __init__(self):
        self.markdowns = []
        self.captions = []
        self.infos = []

    def markdown(self, text, **kwargs):  # pragma: no cover - trivial
        self.markdowns.append(text)

    def caption(self, text, **kwargs):  # pragma: no cover - trivial
        self.captions.append(text)

    def info(self, text, **kwargs):  # pragma: no cover - trivial
        self.infos.append(text)


def _setup(monkeypatch):
    st = ST()
    monkeypatch.setattr(ui, "st", st)
    monkeypatch.setattr(ui, "_load_vocab_sheet", lambda *a, **k: None)
    return st


def test_vocab_lookup_context_label(monkeypatch):
    st = _setup(monkeypatch)
    ui.render_vocab_lookup("k", context_label="Day 1 Chapter 2")
    assert st.markdowns[0] == "#### 📖 Mini Dictionary – Day 1 Chapter 2"


def test_vocab_lookup_no_label(monkeypatch):
    st = _setup(monkeypatch)
    ui.render_vocab_lookup("k")
    assert st.markdowns[0] == "#### 📖 Mini Dictionary"
