"""Helpers for writing inventory data to Firestore workspaces.

The current Streamlit code base has a number of ad-hoc Firestore writes. The
inventory dashboard (products, receiving stock, and selling stock) needs every
write to live under ``default/workspaces/<collection>`` so that each store
remains isolated even though all entries share the same sub-collection.  Every
document also carries ``workspace_uid`` so that the dashboard can filter rows
per store without having to duplicate the workspace in the Firestore path.
"""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Optional


class _CollectionLike:  # pragma: no cover - runtime duck type helper
    def document(self, document_id: str) -> "_DocumentLike": ...

    def collection(self, name: str) -> "_CollectionLike": ...

    def add(self, document_data: Mapping[str, Any]): ...


class _DocumentLike:  # pragma: no cover - runtime duck type helper
    def collection(self, name: str) -> _CollectionLike: ...

    def set(self, document_data: Mapping[str, Any]): ...


class _DatabaseLike:  # pragma: no cover - runtime duck type helper
    def collection(self, name: str) -> _CollectionLike: ...


def _workspace_collection(
    db: _DatabaseLike, workspace_uid: str, collection_name: str
) -> _CollectionLike:
    """Return the nested collection ``default/workspaces/<collection_name>``.

    Args:
        db: Firestore database client.
        workspace_uid: The workspace identifier coming from the authenticated
            user.
        collection_name: The terminal collection name (``products``, ``sell``
            or ``receive``).

    Raises:
        ValueError: If ``workspace_uid`` is empty.
    """

    if not workspace_uid:
        raise ValueError("workspace_uid is required")
    return (
        db.collection("default")
        .document("workspaces")
        .collection(collection_name)
    )


def _prepare_payload(
    workspace_uid: str, payload: Mapping[str, Any]
) -> MutableMapping[str, Any]:
    """Return a mutable copy that always contains ``workspace_uid``."""

    prepared: MutableMapping[str, Any] = dict(payload)
    prepared["workspace_uid"] = workspace_uid
    return prepared


def _persist(
    collection: _CollectionLike,
    workspace_uid: str,
    payload: Mapping[str, Any],
    *,
    document_id: Optional[str] = None,
):
    """Persist ``payload`` either via ``set`` or ``add``.

    When ``document_id`` is provided we assume the caller wants a specific
    document path. Otherwise we fall back to the ``add`` helper which lets
    Firestore generate the ID for us.
    """

    data = _prepare_payload(workspace_uid, payload)
    if document_id:
        doc = collection.document(document_id)
        doc.set(data)
        return doc
    return collection.add(data)


def save_product(
    db: _DatabaseLike,
    workspace_uid: str,
    payload: Mapping[str, Any],
    *,
    document_id: Optional[str] = None,
):
    """Persist a product definition for the given workspace."""

    collection = _workspace_collection(db, workspace_uid, "products")
    return _persist(collection, workspace_uid, payload, document_id=document_id)


def save_sell(
    db: _DatabaseLike,
    workspace_uid: str,
    payload: Mapping[str, Any],
    *,
    document_id: Optional[str] = None,
):
    """Persist a sale record for the given workspace."""

    collection = _workspace_collection(db, workspace_uid, "sell")
    return _persist(collection, workspace_uid, payload, document_id=document_id)


def save_receive(
    db: _DatabaseLike,
    workspace_uid: str,
    payload: Mapping[str, Any],
    *,
    document_id: Optional[str] = None,
):
    """Persist a stock receiving record for the given workspace."""

    collection = _workspace_collection(db, workspace_uid, "receive")
    return _persist(collection, workspace_uid, payload, document_id=document_id)

