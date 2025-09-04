from unittest.mock import MagicMock

from src import youtube


def test_fetch_youtube_playlist_videos_success(monkeypatch):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "items": [{"snippet": {"resourceId": {"videoId": "abc123"}, "title": "My Video"}}]
    }
    mock_get = MagicMock(return_value=mock_resp)
    monkeypatch.setattr(youtube.requests, "get", mock_get)

    def noop_cache(ttl=None):
        def decorator(fn):
            return fn
        return decorator

    monkeypatch.setattr(youtube.st, "cache_data", noop_cache)
    videos = youtube.fetch_youtube_playlist_videos("PL123", api_key="KEY")
    mock_get.assert_called_once()
    url = mock_get.call_args[0][0]
    params = mock_get.call_args[1]["params"]
    assert url == "https://www.googleapis.com/youtube/v3/playlistItems"
    assert params["playlistId"] == "PL123"
    assert params["key"] == "KEY"
    assert videos == [{"title": "My Video", "url": "https://www.youtube.com/watch?v=abc123"}]


def test_get_playlist_ids_for_level_fallback(monkeypatch):
    monkeypatch.setattr(youtube.st, "info", MagicMock())
    result = youtube.get_playlist_ids_for_level("C1")
    expected = youtube.YOUTUBE_PLAYLIST_IDS[youtube.DEFAULT_PLAYLIST_LEVEL]
    assert result == expected
    youtube.st.info.assert_called_once()
