import ast
import importlib
import pathlib
import sys
import types
from unittest.mock import MagicMock

import pytest


def load_playlist_module():
    path = pathlib.Path(__file__).resolve().parents[1] / 'a1sprechen.py'
    source = path.read_text()
    module_ast = ast.parse(source)
    nodes = []
    for node in module_ast.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id in {
                    'DEFAULT_PLAYLIST_LEVEL',
                    'YOUTUBE_PLAYLIST_IDS',
                    'YOUTUBE_API_KEY',
                }:
                    nodes.append(node)
                    break
        elif isinstance(node, ast.FunctionDef) and node.name in {
            'get_playlist_ids_for_level',
            'fetch_youtube_playlist_videos',
        }:
            nodes.append(node)
    mod = types.ModuleType('playlist_module')
    st_mock = MagicMock()
    def cache_data(ttl=None):
        def decorator(fn):
            return fn
        return decorator
    st_mock.cache_data = cache_data
    mod.st = st_mock
    import requests
    mod.requests = requests
    mod.random = __import__('random')
    code = compile(ast.Module(body=nodes, type_ignores=[]), 'playlist', 'exec')
    exec(code, mod.__dict__)
    return mod


@pytest.fixture()
def playlist_module():
    return load_playlist_module()


def test_fetch_youtube_playlist_videos_success(monkeypatch, playlist_module):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'items': [
            {
                'snippet': {
                    'resourceId': {'videoId': 'abc123'},
                    'title': 'My Video',
                }
            }
        ]
    }
    mock_get = MagicMock(return_value=mock_response)
    monkeypatch.setattr(playlist_module.requests, 'get', mock_get)

    videos = playlist_module.fetch_youtube_playlist_videos('PL123', api_key='KEY')

    mock_get.assert_called_once()
    called_url = mock_get.call_args[0][0]
    called_params = mock_get.call_args[1]['params']
    assert called_url == 'https://www.googleapis.com/youtube/v3/playlistItems'
    assert called_params['playlistId'] == 'PL123'
    assert called_params['key'] == 'KEY'
    assert videos == [{
        'title': 'My Video',
        'url': 'https://www.youtube.com/watch?v=abc123',
    }]


def test_get_playlist_ids_for_level_fallback(monkeypatch, playlist_module):
    monkeypatch.setattr(playlist_module.st, 'info', MagicMock())
    result = playlist_module.get_playlist_ids_for_level('C1')
    expected = playlist_module.YOUTUBE_PLAYLIST_IDS[playlist_module.DEFAULT_PLAYLIST_LEVEL]
    assert result == expected
    playlist_module.st.info.assert_called_once()


@pytest.fixture()
def data_loading(monkeypatch):
    import streamlit as st

    monkeypatch.setattr(st, "secrets", {})

    def cache_data(ttl=None):
        def decorator(fn):
            return fn

        return decorator

    monkeypatch.setattr(st, "cache_data", cache_data)
    monkeypatch.setattr(st, "error", MagicMock())
    monkeypatch.setattr(st, "warning", MagicMock())
    monkeypatch.setattr(st, "info", MagicMock())

    root = pathlib.Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    import src.data_loading as dl

    importlib.reload(dl)
    return dl


def test_load_student_data_handles_mixed_case_headers(monkeypatch, data_loading):
    csv = (
        " Contract_End , student_code ,EMAIL\n"
        "12/31/2024, ABC123 ,Test@Example.com\n"
    )
    mock_resp = MagicMock()
    mock_resp.text = csv
    mock_resp.raise_for_status = lambda: None
    monkeypatch.setattr(
        data_loading.requests, "get", lambda *args, **kwargs: mock_resp
    )

    df = data_loading.load_student_data()

    assert df is not None
    assert list(df.columns) == ["ContractEnd", "StudentCode", "Email"]
    assert df.loc[0, "StudentCode"] == "abc123"
    assert df.loc[0, "Email"] == "test@example.com"
