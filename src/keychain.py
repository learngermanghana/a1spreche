from __future__ import annotations

from enum import Enum


class KeychainKey(str, Enum):
    accessToken = "accessToken"
    refreshToken = "refreshToken"


def delete_token(key: KeychainKey) -> None:
    """Remove a token from the platform keychain.

    The real application relies on a Swift helper to manage secure
    storage.  During tests this function is a no-op so the logout flow
    can invoke it unconditionally.
    """

    try:
        # The Swift implementation is not available in tests.
        # In production this function would call into KeychainHelper.
        pass
    except Exception:
        # Ignore any issue to avoid breaking logout cleanup.
        pass


# Provide a camelCase alias for parity with the Swift helper.
deleteToken = delete_token

__all__ = ["KeychainKey", "delete_token", "deleteToken"]
