from src import pdf_utils


def test_load_school_logo_prefers_local(tmp_path, monkeypatch):
    local = tmp_path / "logo.png"
    local.write_bytes(b"local")
    monkeypatch.setattr(pdf_utils, "LOCAL_LOGO", local)
    monkeypatch.setattr(pdf_utils, "CACHE_LOGO", tmp_path / "school_logo.png")

    called = False

    def fake_get(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("network should not be called")

    monkeypatch.setattr(pdf_utils.requests, "get", fake_get)
    path = pdf_utils.load_school_logo()
    assert path == str(local)
    assert called is False


def test_load_school_logo_uses_cache(tmp_path, monkeypatch):
    cache = tmp_path / "school_logo.png"
    cache.write_bytes(b"cache")
    monkeypatch.setattr(pdf_utils, "LOCAL_LOGO", tmp_path / "missing.png")
    monkeypatch.setattr(pdf_utils, "CACHE_LOGO", cache)

    called = False

    def fake_get(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("network should not be called")

    monkeypatch.setattr(pdf_utils.requests, "get", fake_get)
    path = pdf_utils.load_school_logo()
    assert path == str(cache)
    assert called is False


def test_load_school_logo_downloads_when_needed(tmp_path, monkeypatch):
    cache = tmp_path / "school_logo.png"
    monkeypatch.setattr(pdf_utils, "LOCAL_LOGO", tmp_path / "missing.png")
    monkeypatch.setattr(pdf_utils, "CACHE_LOGO", cache)

    class Resp:
        content = b"net"

        def raise_for_status(self):
            pass

    monkeypatch.setattr(pdf_utils.requests, "get", lambda *a, **k: Resp())
    path = pdf_utils.load_school_logo()
    assert path == str(cache)
    assert cache.read_bytes() == b"net"
