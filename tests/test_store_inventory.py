from __future__ import annotations

from typing import Any, List, Mapping, MutableMapping

import pytest

from src import store_inventory


class _Recorder:
    def __init__(self):
        self.calls: List[Any] = []


class _FakeCollection:
    def __init__(self, path: str, recorder: _Recorder):
        self._path = path
        self._recorder = recorder

    def collection(self, name: str) -> "_FakeCollection":
        return _FakeCollection(f"{self._path}/{name}", self._recorder)

    def document(self, document_id: str) -> "_FakeDocument":
        return _FakeDocument(f"{self._path}/{document_id}", self._recorder)

    def add(self, payload: Mapping[str, Any]):
        self._recorder.calls.append(("add", self._path, dict(payload)))
        return (self._path, payload)


class _FakeDocument:
    def __init__(self, path: str, recorder: _Recorder):
        self._path = path
        self._recorder = recorder

    def set(self, payload: Mapping[str, Any]):
        self._recorder.calls.append(("set", self._path, dict(payload)))
        return self

    def collection(self, name: str) -> _FakeCollection:
        return _FakeCollection(f"{self._path}/{name}", self._recorder)


class _FakeDB:
    def __init__(self):
        self._recorder = _Recorder()

    @property
    def calls(self) -> List[Any]:
        return self._recorder.calls

    def collection(self, name: str) -> _FakeCollection:
        return _FakeCollection(name, self._recorder)


def _assert_workspace_uid(payload: MutableMapping[str, Any], uid: str):
    assert payload["workspace_uid"] == uid


def test_save_product_writes_under_workspace_and_sets_uid():
    db = _FakeDB()

    store_inventory.save_product(
        db, workspace_uid="store-123", payload={"name": "Orange"}, document_id="sku-1"
    )

    action, path, payload = db.calls[0]
    assert action == "set"
    assert path == "workspaces/store-123/products/sku-1"
    _assert_workspace_uid(payload, "store-123")
    assert payload["name"] == "Orange"


def test_save_sell_uses_add_when_document_id_missing():
    db = _FakeDB()

    store_inventory.save_sell(db, "tenant-a", {"qty": 2})

    action, path, payload = db.calls[0]
    assert action == "add"
    assert path == "workspaces/tenant-a/sell"
    _assert_workspace_uid(payload, "tenant-a")
    assert payload["qty"] == 2


def test_save_receive_overrides_existing_workspace_uid():
    db = _FakeDB()

    store_inventory.save_receive(
        db,
        "alpha",
        {"workspace_uid": "beta", "qty": 12},
        document_id="receipt-77",
    )

    _, _, payload = db.calls[0]
    _assert_workspace_uid(payload, "alpha")
    assert payload["qty"] == 12


def test_workspace_uid_required():
    db = _FakeDB()
    with pytest.raises(ValueError):
        store_inventory.save_product(db, "", {"name": "Widget"})

