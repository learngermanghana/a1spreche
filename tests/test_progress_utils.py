from src import progress_utils

def test_save_last_position(monkeypatch):
    saved = {}

    class DummyRef:
        def set(self, data, *, merge):
            saved.update(data)
            saved['merge'] = merge

    monkeypatch.setattr(progress_utils, "_progress_doc_ref", lambda code: DummyRef())

    progress_utils.save_last_position("stu", 5)
    assert saved == {"last_position": 5, "merge": True}


def test_load_last_position_roundtrip(monkeypatch):
    class DummySnap:
        def __init__(self, exists, data):
            self.exists = exists
            self._data = data

        def to_dict(self):
            return self._data

    class DummyRef:
        def __init__(self, snap):
            self.snap = snap
            self.saved = None

        def get(self):
            return self.snap

        def set(self, data, *, merge):
            self.saved = data

    # existing progress
    ref = DummyRef(DummySnap(True, {"last_position": 3}))
    monkeypatch.setattr(progress_utils, "_progress_doc_ref", lambda code: ref)
    assert progress_utils.load_last_position("stu") == 3

    # missing document initialises to 0 and saves it
    ref2 = DummyRef(DummySnap(False, {}))
    monkeypatch.setattr(progress_utils, "_progress_doc_ref", lambda code: ref2)
    assert progress_utils.load_last_position("stu") == 0
    assert ref2.saved == {"last_position": 0}
