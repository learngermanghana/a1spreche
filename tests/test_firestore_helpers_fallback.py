import importlib
import sys
import types

from google.api_core.exceptions import FailedPrecondition

from src.firestore_helpers import stream_latest_snapshots


class StubSnapshot:
    def __init__(self, created_at, payload):
        self._data = {"created_at": created_at, "payload": payload}
        self.reference = f"ref-{payload}"

    def to_dict(self):
        return dict(self._data)


class StubQuery:
    def __init__(self, snapshots):
        self._snapshots = list(snapshots)

    def where(self, *args, **kwargs):  # pragma: no cover - chaining support
        return self

    def order_by(self, *args, **kwargs):
        raise FailedPrecondition("missing index for order")

    def limit(self, *args, **kwargs):  # pragma: no cover - not used in fallback
        return self

    def stream(self):
        return list(self._snapshots)


def test_stream_latest_snapshots_handles_failed_precondition():
    docs = [
        StubSnapshot(2, "middle"),
        StubSnapshot(5, "latest"),
        StubSnapshot(1, "earliest"),
    ]
    query = StubQuery(docs)

    results = stream_latest_snapshots(query, "created_at", limit=1)

    assert len(results) == 1
    snapshot, data = results[0]
    assert snapshot is docs[1]
    assert data["payload"] == "latest"


def test_stream_latest_snapshots_import_without_firestore(monkeypatch):
    import src.firestore_helpers as helpers

    with monkeypatch.context() as m:
        stub_firebase = types.ModuleType("firebase_admin")
        m.setitem(sys.modules, "firebase_admin", stub_firebase)

        stub_google = types.ModuleType("google")
        stub_google.__path__ = []  # type: ignore[attr-defined]
        stub_cloud = types.ModuleType("google.cloud")
        stub_cloud.__path__ = []  # type: ignore[attr-defined]
        stub_firestore_v1 = types.ModuleType("google.cloud.firestore_v1")

        stub_google.cloud = stub_cloud  # type: ignore[attr-defined]
        stub_cloud.firestore_v1 = stub_firestore_v1  # type: ignore[attr-defined]

        m.setitem(sys.modules, "google", stub_google)
        m.setitem(sys.modules, "google.cloud", stub_cloud)
        m.setitem(sys.modules, "google.cloud.firestore_v1", stub_firestore_v1)

        reloaded = importlib.reload(helpers)

        assert callable(reloaded.stream_latest_snapshots)
        assert getattr(reloaded.firestore.Query, "DESCENDING", None) is not None

    importlib.reload(helpers)
