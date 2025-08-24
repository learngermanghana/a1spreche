import ast
import logging
from pathlib import Path

from google.api_core.exceptions import GoogleAPICallError


def _load_function():
    source = Path(__file__).resolve().parents[1] / "a1sprechen.py"
    mod = ast.parse(source.read_text())
    func = next(
        node for node in mod.body if isinstance(node, ast.FunctionDef) and node.name == "get_schreiben_stats"
    )
    namespace = {}
    class DummyDoc:
        def get(self):
            raise GoogleAPICallError("boom")
    class DummyCollection:
        def document(self, *args, **kwargs):
            return DummyDoc()
    class DummyDB:
        def collection(self, *args, **kwargs):
            return DummyCollection()
    namespace["db"] = DummyDB()
    namespace["GoogleAPICallError"] = GoogleAPICallError
    namespace["logging"] = logging
    exec(ast.unparse(func), namespace)
    return namespace["get_schreiben_stats"]


def test_get_schreiben_stats_returns_default_on_error(caplog):
    get_stats = _load_function()
    with caplog.at_level(logging.ERROR):
        result = get_stats("abc")
    assert result == {
        "total": 0,
        "passed": 0,
        "average_score": 0,
        "best_score": 0,
        "pass_rate": 0,
        "last_attempt": None,
        "attempts": [],
        "last_letter": "",
    }
    assert any(record.levelno == logging.ERROR for record in caplog.records)
