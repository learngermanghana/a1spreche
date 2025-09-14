import types

from src import data_loading


def _make_response(text: str):
    return types.SimpleNamespace(text=text, raise_for_status=lambda: None)


def test_class_column_renamed(monkeypatch):
    csv = "StudentCode,Class,ContractEnd\nsc1,Test Class,2025-01-01\n"

    # ensure cache is clear so our patched request is used
    data_loading._load_student_data_cached.clear()

    monkeypatch.setattr(data_loading.requests, "get", lambda url, timeout=12: _make_response(csv))

    df = data_loading.load_student_data()
    assert df is not None
    assert "ClassName" in df.columns
    assert df.loc[0, "ClassName"] == "Test Class"
