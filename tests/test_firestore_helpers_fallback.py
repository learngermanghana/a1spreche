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
