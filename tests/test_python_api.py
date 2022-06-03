from pathlib import Path

import pytest
from lmdb_python import lmdb_c
from lmdb_python.core import Database


def test_create_db(tmp_path: Path):
    Database(str(tmp_path))


@pytest.fixture
def db(tmp_path: Path):
    return Database(str(tmp_path))


def test_put(db: Database):
    db.put(b"key", b"value")


@pytest.fixture
def db_with_data(tmp_path: Path):
    db = Database(str(tmp_path))
    db.put(b"key", b"value")
    return db


def test_get(db_with_data: Database):
    assert db_with_data.get(b"key") == b"value"


def test_delete(db_with_data: Database):
    db_with_data.delete(b"key")
    with pytest.raises(lmdb_c.LmdbException) as e:
        db_with_data.get(b"key")
    assert e.value.rc == lmdb_c.MDB_NOTFOUND
