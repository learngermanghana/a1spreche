import ast
import logging
import textwrap
import types
from pathlib import Path


def _load_render_section_any(render_vocab_stub=None):
    """Load the ``render_section_any`` helper from ``a1sprechen.py``.

    Parameters
    ----------
    render_vocab_stub:
        Optional function to substitute for ``render_vocab_lookup`` during tests.
    """
    src_path = Path(__file__).resolve().parents[1] / "a1sprechen.py"
    source = src_path.read_text()
    tree = ast.parse(source)

    class Finder(ast.NodeVisitor):
        def __init__(self):
            self.pos = {}

        def visit_FunctionDef(self, node):
            self.pos[node.name] = (node.lineno, node.end_lineno)
            self.generic_visit(node)

    finder = Finder()
    finder.visit(tree)

    start = finder.pos["_as_list"][0] - 1
    end = finder.pos["render_section_any"][1]
    snippet = textwrap.dedent("\n".join(source.splitlines()[start:end]))

    mod = types.ModuleType("render_section_any_test")

    class ST:
        def __init__(self):
            self.markdowns = []

        def markdown(self, text, **kwargs):  # pragma: no cover - trivial
            self.markdowns.append(text)

        def expander(self, *a, **k):  # pragma: no cover - trivial
            class CM:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    return False

            return CM()

    mod.st = ST()
    mod.render_vocab_lookup = render_vocab_stub or (lambda *a, **k: None)
    mod.render_assignment_reminder = lambda *a, **k: None
    mod.logging = logging

    exec(snippet, mod.__dict__)
    return mod.render_section_any, mod.st


def test_single_dict():
    render_section_any, st = _load_render_section_any()
    day_info = {"lesen": {"chapter": "1"}}
    render_section_any(day_info, "lesen", "Lesen", "📖", set())
    assert st.markdowns == ["#### 📖 Lesen"]


def test_list_of_dicts_with_invalid(caplog):
    render_section_any, st = _load_render_section_any()
    bad = {"lesen": [{"chapter": "1"}, "oops", {"chapter": "2"}]}
    with caplog.at_level(logging.WARNING):
        render_section_any(bad, "lesen", "Lesen", "📖", set())
    assert st.markdowns[0] == "#### 📖 Lesen"
    assert "Part 1 of 2" in st.markdowns[1]
    assert "Part 2 of 2" in st.markdowns[2]
    assert "skipping non-dict entries" in caplog.text


def test_malformed_input(caplog):
    render_section_any, st = _load_render_section_any()
    with caplog.at_level(logging.WARNING):
        render_section_any({"lesen": 123}, "lesen", "Lesen", "📖", set())
    assert st.markdowns == []
    assert "Expected dict or list" in caplog.text


def test_dictionary_label_passed():
    captured = {}

    def stub(key, context_label=None):  # pragma: no cover - trivial
        captured["key"] = key
        captured["label"] = context_label

    render_section_any, st = _load_render_section_any(render_vocab_stub=stub)
    day_info = {"lesen": {"chapter": "2", "workbook_link": "x"}, "day": 7}
    render_section_any(day_info, "lesen", "Lesen", "📖", set())

    assert captured == {"key": "lesen-0", "label": "Day 7 Chapter 2"}

