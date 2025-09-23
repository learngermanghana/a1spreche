import threading

from src.auth import st, persist_session_client, get_session_client, clear_session_clients


def test_session_store_thread_safety(monkeypatch):
    """Concurrent writes and reads should be thread safe."""
    monkeypatch.setattr(st, "session_state", {})
    clear_session_clients()
    tokens = [f"tok{i}" for i in range(100)]

    def worker(tok: str) -> None:
        persist_session_client(tok, tok)
        assert get_session_client(tok) == tok

    threads = [threading.Thread(target=worker, args=(tok,)) for tok in tokens]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Ensure all tokens were stored correctly
    assert all(get_session_client(tok) == tok for tok in tokens)
