import pathlib

import pytest

from lmdb_python import lmdb_c


@pytest.fixture(scope="module")
def c_env():
    return lmdb_c.LmdbEnvironment()


def test_create_env(c_env: lmdb_c.LmdbEnvironment):
    assert c_env.create_env() == 0


def test_open_env(c_env: lmdb_c.LmdbEnvironment, tmp_path: pathlib.Path):
    assert c_env.open_env(str(tmp_path)) == 0


@pytest.fixture
def c_txn():
    return lmdb_c.LmdbTransaction()


@pytest.fixture
def c_env_opened(tmp_path: pathlib.Path):
    env = lmdb_c.LmdbEnvironment()
    env.create_env()
    env.open_env(str(tmp_path))
    return env


def test_begin_txn_default(
    c_txn: lmdb_c.LmdbTransaction, c_env_opened: lmdb_c.LmdbEnvironment
):
    assert c_txn.begin_txn(c_env_opened) == 0


@pytest.mark.parametrize("read_only", (True, False))
def test_begin_txn(
    c_txn: lmdb_c.LmdbTransaction, c_env_opened: lmdb_c.LmdbEnvironment, read_only: bool
):
    assert c_txn.begin_txn(c_env_opened, read_only=read_only) == 0


def test_value_empty():
    value = lmdb_c.LmdbValue()
    assert value.to_bytes() is None


@pytest.mark.parametrize(
    "data", (b"123", b"a quick brown fox", "hello".encode("utf-8"))
)
def test_value(data: bytes):
    value = lmdb_c.LmdbValue(data)
    assert value.to_bytes() == data
