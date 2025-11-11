"""Initialize the SQLite database for auth refresh tokens."""

import os
import sqlite3
from pathlib import Path


def init_db(path: str) -> None:
    conn = sqlite3.connect(path)
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                device_id TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id)"
        )
    conn.close()


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    db_path = os.getenv("REFRESH_DB_PATH", str(base_dir / "refresh_tokens.db"))
    init_db(db_path)
    print(f"Initialized refresh token store at {db_path}")


if __name__ == "__main__":  # pragma: no cover - script entrypoint
    main()

