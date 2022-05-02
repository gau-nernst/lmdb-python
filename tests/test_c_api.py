import pathlib
import pickle
from typing import Any, Callable, Iterable, NewType, Tuple

import pytest
from lmdb_python import errors, lmdb_c


def test_create_env():
    env = lmdb_c.LmdbEnvironment()
    assert env.create_env() == 0
    env.close_env()


def test_open_env_default(tmp_path: pathlib.Path):
    env = lmdb_c.LmdbEnvironment()
    env.create_env()
    assert env.open_env(str(tmp_path)) == 0
    env.close_env()


# test no_subdir and read_only
# TODO: how to open env in read_only mode
@pytest.mark.parametrize("no_subdir", (True, False))
def test_open_env(tmp_path: pathlib.Path, no_subdir: bool):
    env = lmdb_c.LmdbEnvironment()
    env.create_env()
    env_path = str(tmp_path / "test_lmdb") if no_subdir else str(tmp_path)
    assert env.open_env(env_path, no_subdir=no_subdir) == 0


@pytest.fixture
def opened_env(tmp_path: pathlib.Path):
    env = lmdb_c.LmdbEnvironment()
    env.create_env()
    env.open_env(str(tmp_path))
    yield env
    env.close_env()


def test_begin_txn_default(opened_env: lmdb_c.LmdbEnvironment):
    txn = lmdb_c.LmdbTransaction()
    assert txn.begin_txn(opened_env) == 0
    # check default is read_only


@pytest.mark.parametrize("read_only", (True, False))
def test_begin_txn(opened_env: lmdb_c.LmdbEnvironment, read_only: bool):
    txn = lmdb_c.LmdbTransaction()
    assert txn.begin_txn(opened_env, read_only=read_only) == 0
    # check read_only state


@pytest.fixture
def make_txn(opened_env: lmdb_c.LmdbEnvironment):
    def _make_txn(read_only: bool):
        txn = lmdb_c.LmdbTransaction()
        txn.begin_txn(opened_env, read_only=read_only)
        return txn

    return _make_txn


def test_open_dbi(make_txn: Callable[[bool], lmdb_c.LmdbTransaction]):
    dbi = lmdb_c.LmdbDatabase()
    txn = make_txn(True)
    assert dbi.open_dbi(txn) == 0


def test_value_empty():
    value = lmdb_c.LmdbValue()
    assert value.to_bytes() is None


@pytest.mark.parametrize(
    "data", (b"123", b"a quick brown fox", "hello".encode("utf-8"))
)
def test_value(data: bytes):
    value = lmdb_c.LmdbValue(data)
    assert value.to_bytes() == data


@pytest.mark.parametrize("data", ("a string", 100, list()))
def test_value_type_error(data: Any):
    with pytest.raises(TypeError):
        lmdb_c.LmdbValue(data)


key_samples = (b"key123", "u1234532".encode("utf-8"))
value_samples = (b"value456", pickle.dumps(["1", 12, "Engineer"]))
key_value_samples = tuple(zip(key_samples, value_samples))


@pytest.mark.parametrize("key,value", key_value_samples)
def test_put(
    key: bytes,
    value: bytes,
    make_txn: Callable[[bool], lmdb_c.LmdbTransaction],
):
    txn = make_txn(False)
    dbi = lmdb_c.LmdbDatabase()
    dbi.open_dbi(txn)

    c_key = lmdb_c.LmdbValue(key)
    c_value = lmdb_c.LmdbValue(value)
    assert lmdb_c.put(c_key, c_value, txn, dbi) == 0
    assert txn.commit_txn() == 0


KeyValue = NewType("KeyValue", Tuple[bytes, bytes])


@pytest.fixture
def make_dbi_with_data(make_txn: Callable[[bool], lmdb_c.LmdbTransaction]):
    def _make_dbi_with_data(data: Iterable[KeyValue]):
        txn = make_txn(False)
        dbi = lmdb_c.LmdbDatabase()
        dbi.open_dbi(txn)

        for key, value in data:
            c_key = lmdb_c.LmdbValue(key)
            c_value = lmdb_c.LmdbValue(value)
            lmdb_c.put(c_key, c_value, txn, dbi)
        txn.commit_txn()
        return dbi

    return _make_dbi_with_data


@pytest.mark.parametrize("key,value", key_value_samples)
def test_get(
    key: bytes,
    value: bytes,
    make_dbi_with_data: Callable[[Iterable[KeyValue]], lmdb_c.LmdbDatabase],
    make_txn: Callable[[bool], lmdb_c.LmdbTransaction],
):
    dbi = make_dbi_with_data([(key, value)])
    txn = make_txn(True)

    c_key = lmdb_c.LmdbValue(key)
    c_value = lmdb_c.LmdbValue()
    assert lmdb_c.get(c_key, c_value, txn, dbi) == 0
    assert c_value.to_bytes() == value


@pytest.mark.parametrize("key", key_samples)
def test_get_notfound(
    key: bytes,
    make_txn: Callable[[bool], lmdb_c.LmdbTransaction],
):
    txn = make_txn(True)
    dbi = lmdb_c.LmdbDatabase()
    dbi.open_dbi(txn)

    c_key = lmdb_c.LmdbValue(key)
    c_value = lmdb_c.LmdbValue()
    assert lmdb_c.get(c_key, c_value, txn, dbi) == lmdb_c.MDB_NOTFOUND


@pytest.mark.parametrize("key,value", key_value_samples)
def test_delete(
    key: bytes,
    value: bytes,
    make_dbi_with_data: Callable[[Iterable[KeyValue]], lmdb_c.LmdbDatabase],
    make_txn: Callable[[bool], lmdb_c.LmdbTransaction],
):
    dbi = make_dbi_with_data([(key, value)])
    txn = make_txn(False)

    c_key = lmdb_c.LmdbValue(key)
    c_value = lmdb_c.LmdbValue()
    assert lmdb_c.get(c_key, c_value, txn, dbi) == 0

    assert lmdb_c.delete(c_key, txn, dbi) == 0
    assert txn.commit_txn() == 0

    txn = make_txn(True)
    assert lmdb_c.get(c_key, c_value, txn, dbi) == lmdb_c.MDB_NOTFOUND
