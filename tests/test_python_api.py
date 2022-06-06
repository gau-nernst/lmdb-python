import concurrent.futures
from pathlib import Path
from typing import List

import pytest
from lmdb_python import Database, LmdbEnvFlags, lmdb_c


def test_create_db(tmp_path: Path):
    Database(str(tmp_path))


@pytest.fixture
def db(tmp_path: Path):
    return Database(str(tmp_path))


def test_put(db: Database):
    db.put(b"key", b"value")


@pytest.fixture
def db_with_data(db):
    db.put(b"key", b"value")
    return db


def test_get(db_with_data: Database):
    assert db_with_data.get(b"key") == b"value"


def test_delete(db_with_data: Database):
    db_with_data.delete(b"key")
    with pytest.raises(lmdb_c.LmdbException) as e:
        db_with_data.get(b"key")
    assert e.value.rc == lmdb_c.MDB_NOTFOUND


@pytest.fixture
def keys_100():
    return [f"key_{i}".encode() for i in range(100)]


@pytest.fixture
def values_100():
    return [f"value_{i}".encode() for i in range(100)]


def test_put_batch(db: Database, keys_100: List[bytes], values_100: List[bytes]):
    db.put_batch(zip(keys_100, values_100))


@pytest.fixture
def db_with_data_100(db: Database, keys_100: List[bytes], values_100: List[bytes]):
    db.put_batch(zip(keys_100, values_100))
    return db


def test_get_batch(
    db_with_data_100: Database, keys_100: List[bytes], values_100: List[bytes]
):
    values = db_with_data_100.get_batch(keys_100)
    for v1, v2 in zip(values, values_100):
        assert v1 == v2


def test_delete_batch(db_with_data_100: Database, keys_100: List[bytes]):
    db_with_data_100.delete_batch(keys_100)
    for k in keys_100:
        with pytest.raises(lmdb_c.LmdbException) as e:
            db_with_data_100.get(k)
        assert e.value.rc == lmdb_c.MDB_NOTFOUND


def test_get_multithreading(
    tmp_path: Path, db_with_data_100: Database, keys_100: List[bytes]
):
    def create_worker(keys: List[bytes], tmp_path: Path):
        flags = LmdbEnvFlags(read_only=True)
        db_thread = Database(str(tmp_path), flags=flags)
        for k in keys:
            db_thread.get(k)

    N = 10
    with concurrent.futures.ThreadPoolExecutor(max_workers=N) as executor:
        futures = [executor.submit(create_worker, keys_100, tmp_path) for _ in range(N)]
        for f in futures:
            f.result()


def test_get_multiprocessing(db_with_data_100: Database, keys_100: List[bytes]):
    N = 10
    with concurrent.futures.ProcessPoolExecutor(max_workers=N) as executor:
        results = executor.map(db_with_data_100.get, keys_100)
        for _ in results:
            pass
