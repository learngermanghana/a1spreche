import types
from pathlib import Path

import pytest
from src import data_loading


def _make_response(text: str):
    return types.SimpleNamespace(text=text, raise_for_status=lambda: None)


BASE_ROSTER = Path(__file__).with_name("data").joinpath("roster_base.csv")


@pytest.mark.parametrize(
    "label",
    [
        "Class",
        "classname",
        "Classroom",
        "class_name",
        "Group",
        "Course",
    ],
)
def test_class_column_variants(monkeypatch, label):
    csv = BASE_ROSTER.read_text().replace("ClassName", label)

    # ensure cache is clear so our patched request is used
    data_loading._load_student_data_cached.clear()

    monkeypatch.setattr(
        data_loading.requests,
        "get",
        lambda url, timeout=12: _make_response(csv),
    )

    df = data_loading.load_student_data()
    assert df is not None
    assert "ClassName" in df.columns
    assert df.loc[0, "ClassName"] == "Test Class"


def test_missing_class_column_raises(monkeypatch):
    csv = BASE_ROSTER.read_text().replace("ClassName", "Room")
    data_loading._load_student_data_cached.clear()
    monkeypatch.setattr(
        data_loading.requests,
        "get",
        lambda url, timeout=12: _make_response(csv),
    )
    with pytest.raises(ValueError) as exc:
        data_loading.load_student_data()
    assert "Supported column names" in str(exc.value)
