import pandas as pd

from src.assignment_ui import get_enrollment_dates


def test_get_enrollment_dates(monkeypatch):
    df = pd.DataFrame([
        {
            "StudentCode": "abc",
            "ContractStart": "2024-01-01",
            "ContractEnd": "2024-06-30",
        }
    ])
    monkeypatch.setattr("src.assignment_ui.load_student_data", lambda: df)
    start, end = get_enrollment_dates("abc")
    assert start == "2024-01-01"
    assert end == "2024-06-30"


def test_get_enrollment_dates_missing(monkeypatch):
    monkeypatch.setattr("src.assignment_ui.load_student_data", lambda: None)
    start, end = get_enrollment_dates("zzz")
    assert start == "" and end == ""
