import importlib
import logging
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from google.api_core.exceptions import GoogleAPICallError

import src.schreiben as schreiben

def test_get_schreiben_stats_returns_default_on_error(monkeypatch, caplog):
    mod = importlib.reload(schreiben)
    mock_db = MagicMock()
    mock_doc = mock_db.collection.return_value.document.return_value
    mock_doc.get.side_effect = GoogleAPICallError("boom")
    monkeypatch.setattr(mod, "db", mock_db)
    with caplog.at_level(logging.ERROR):
        result = mod.get_schreiben_stats("abc")
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
