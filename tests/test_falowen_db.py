import os

from falowen import db


def test_sprechen_usage_with_temp_db(tmp_path):
    db_file = tmp_path / "test.db"
    db.init_db(db_path=str(db_file))

    assert db.get_sprechen_usage("stu", db_path=str(db_file)) == 0
    db.inc_sprechen_usage("stu", db_path=str(db_file))
    assert db.get_sprechen_usage("stu", db_path=str(db_file)) == 1
    assert db.has_sprechen_quota("stu", limit=1, db_path=str(db_file)) is False


def test_get_connection_env_var(tmp_path, monkeypatch):
    env_db = tmp_path / "env.db"
    monkeypatch.setenv("FALOWEN_DB_PATH", str(env_db))
    with db.get_connection() as conn:
        conn.execute("CREATE TABLE t (id INTEGER)")
    assert os.path.exists(env_db)
