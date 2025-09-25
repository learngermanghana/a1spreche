import pytest

from src import youtube


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


@pytest.fixture(autouse=True)
def clear_cache():
    youtube.fetch_youtube_playlist_videos.clear()
    yield
    youtube.fetch_youtube_playlist_videos.clear()


def test_fetch_youtube_playlist_videos_includes_trimmed_description(monkeypatch):
    long_description = " ".join(["Wort"] * 80)
    payload = {
        "items": [
            {
                "snippet": {
                    "title": "Erstes Video",
                    "description": long_description,
                    "resourceId": {"videoId": "abc123"},
                }
            },
            {
                "snippet": {
                    "title": "Zweites Video",
                    "description": " ",
                    "resourceId": {"videoId": "def456"},
                }
            },
        ]
    }

    def fake_get(url, params=None, timeout=None):
        assert "playlistItems" in url
        return DummyResponse(payload)

    monkeypatch.setattr(youtube.requests, "get", fake_get)

    videos = youtube.fetch_youtube_playlist_videos("playlist123", api_key="fake")

    assert len(videos) == 2
    first_video = videos[0]
    assert first_video["title"] == "Erstes Video"
    assert first_video["url"].endswith("abc123")
    assert first_video["description"]
    assert len(first_video["description"]) <= 200
    assert first_video["description"].endswith("…")

    second_video = videos[1]
    assert second_video["description"] is None
