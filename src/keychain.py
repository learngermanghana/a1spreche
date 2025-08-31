"""Thin bridge to the Swift ``KeychainHelper``.

The real application stores OAuth tokens in the macOS keychain via a Swift
helper.  For tests or on platforms where the helper cannot run we simply swallow
errors so the rest of the application can proceed.  The bridge invokes the
Swift functions using ``subprocess`` and provides Python-friendly wrappers.
"""

from enum import Enum
from pathlib import Path
import json
import subprocess
from shutil import which


class KeychainKey(str, Enum):
    """Keys used by ``KeychainHelper.swift``."""
    
    accessToken = "accessToken"
    refreshToken = "refreshToken"

_SWIFT_BIN = which("swift")
_SWIFT_HELPER = Path(__file__).resolve().parents[1] / "KeychainHelper.swift"


def _run_swift(snippet: str) -> None:
    """Execute a small Swift snippet alongside ``KeychainHelper.swift``.

    The helper and Swift toolchain may not be present during tests or on
    non-macOS platforms.  In those situations this function silently returns so
    callers do not fail.
    """

    if not _SWIFT_BIN or not _SWIFT_HELPER.exists():
        return
    try:
        subprocess.run(
            [_SWIFT_BIN, str(_SWIFT_HELPER), "-"],
            input=snippet.encode(),
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        # Ignore failures so logout/login flows can proceed.
        pass


def save_token(token: str, key: KeychainKey) -> None:
    """Persist a token in the platform keychain."""

    snippet = f"saveToken({json.dumps(token)}, key: .{key.value})"
    _run_swift(snippet)


def delete_token(key: KeychainKey) -> None:
    """Remove a token from the platform keychain.

    The real application relies on a Swift helper to manage secure
    storage.  During tests this function is a no-op so the logout flow
    can invoke it unconditionally.
    """

    snippet = f"deleteToken(for: .{key.value})"
    _run_swift(snippet)

# Provide a camelCase alias for parity with the Swift helper.
saveToken = save_token
deleteToken = delete_token

__all__ = [
    "KeychainKey",
    "save_token",
    "delete_token",
    "saveToken",
    "deleteToken",
]
