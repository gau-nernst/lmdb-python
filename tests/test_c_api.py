import pathlib
import pickle
from typing import Any, Callable, Iterable, Tuple

import pytest
from lmdb_python._cython import lmdb_c

lmdb_error_codes = [
    lmdb_c.MDB_KEYEXIST,
    lmdb_c.MDB_NOTFOUND,
    lmdb_c.MDB_PAGE_NOTFOUND,
    lmdb_c.MDB_CORRUPTED,
    lmdb_c.MDB_PANIC,
    lmdb_c.MDB_VERSION_MISMATCH,
    lmdb_c.MDB_INVALID,
    lmdb_c.MDB_MAP_FULL,
    lmdb_c.MDB_DBS_FULL,
    lmdb_c.MDB_READERS_FULL,
    lmdb_c.MDB_TLS_FULL,
    lmdb_c.MDB_TXN_FULL,
    lmdb_c.MDB_CURSOR_FULL,
    lmdb_c.MDB_PAGE_FULL,
    lmdb_c.MDB_MAP_RESIZED,
    lmdb_c.MDB_INCOMPATIBLE,
    lmdb_c.MDB_BAD_RSLOT,
    lmdb_c.MDB_BAD_TXN,
    lmdb_c.MDB_BAD_VALSIZE,
    lmdb_c.MDB_BAD_DBI,
]

_KeyValue = Tuple[bytes, bytes]
_MakeTxn = Callable[..., lmdb_c.LmdbTransaction]
_MakeDbi = Callable[..., lmdb_c.LmdbDatabase]


@pytest.mark.parametrize("error_code", lmdb_error_codes)
def test_error_code(error_code: int):
    error_msg = lmdb_c.strerror(error_code)
    assert isinstance(error_msg, str)


def test_env_init(tmp_path: pathlib.Path):
    lmdb_c.LmdbEnvironment(str(tmp_path))


def test_env_init_no_dir(tmp_path: pathlib.Path):
    invalid_tmp_path = tmp_path / "invalid"
    with pytest.raises(lmdb_c.LmdbException):
        lmdb_c.LmdbEnvironment(str(invalid_tmp_path))


@pytest.mark.parametrize("no_subdir", (True, False))
def test_env_init_no_subdir(tmp_path: pathlib.Path, no_subdir: bool):
    env_path = str(tmp_path / "test_lmdb") if no_subdir else str(tmp_path)
    lmdb_c.LmdbEnvironment(env_path, no_subdir=no_subdir)


@pytest.mark.parametrize("no_subdir", (True, False))
@pytest.mark.parametrize("read_only", (True, False))
def test_env_init_read_only(tmp_path: pathlib.Path, no_subdir: bool, read_only: bool):
    env_path = str(tmp_path / "test_lmdb") if no_subdir else str(tmp_path)
    lmdb_c.LmdbEnvironment(env_path, no_subdir=no_subdir)
    lmdb_c.LmdbEnvironment(env_path, no_subdir=no_subdir, read_only=read_only)


@pytest.fixture
def lmdb_env(tmp_path: pathlib.Path):
    return lmdb_c.LmdbEnvironment(str(tmp_path))


def test_txn_init(lmdb_env: lmdb_c.LmdbEnvironment):
    lmdb_c.LmdbTransaction(lmdb_env)


@pytest.mark.parametrize("read_only", (True, False))
def test_txn_init_read_only(lmdb_env: lmdb_c.LmdbEnvironment, read_only: bool):
    txn = lmdb_c.LmdbTransaction(lmdb_env, read_only=read_only)
    # TODO: check read_only state


@pytest.fixture
def make_txn(lmdb_env: lmdb_c.LmdbEnvironment):
    def _make_txn(read_only: bool) -> lmdb_c.LmdbTransaction:
        return lmdb_c.LmdbTransaction(lmdb_env, read_only=read_only)

    return _make_txn


def test_dbi(make_txn: _MakeTxn):
    txn = make_txn(read_only=True)
    lmdb_c.LmdbDatabase(txn)


def test_data_empty():
    lmdb_data = lmdb_c._LmdbData()
    assert lmdb_data.to_bytes() is None


_bytes_samples = (b"123", b"a quick brown fox", "hello".encode("utf-8"))
_non_bytes_samples = ("a string", 100, list())

_key_samples = (b"key123", "u1234532".encode("utf-8"))
_value_samples = (b"value456", pickle.dumps(["1", 12, "Engineer"]))
_key_value_samples = tuple(zip(_key_samples, _value_samples))


@pytest.mark.parametrize("data", _bytes_samples)
def test_data(data: bytes):
    lmdb_data = lmdb_c._LmdbData(data)
    assert lmdb_data.to_bytes() == data


@pytest.mark.parametrize("data", _non_bytes_samples)
def test_data_type_error(data: Any):
    with pytest.raises(TypeError):
        lmdb_c._LmdbData(data)


@pytest.mark.parametrize("key,value", _key_value_samples)
def test_put(key: bytes, value: bytes, make_txn: _MakeTxn):
    txn = make_txn(read_only=False)
    dbi = lmdb_c.LmdbDatabase(txn)

    dbi.put(key, value, txn)
    txn.commit()


@pytest.fixture
def make_dbi_with_data(make_txn: _MakeTxn):
    def _make_dbi_with_data(data: Iterable[_KeyValue]):
        txn = make_txn(read_only=False)
        dbi = lmdb_c.LmdbDatabase(txn)

        for key, value in data:
            dbi.put(key, value, txn)
        txn.commit()
        return dbi

    return _make_dbi_with_data


@pytest.mark.parametrize("key,value", _key_value_samples)
def test_get(
    key: bytes, value: bytes, make_dbi_with_data: _MakeDbi, make_txn: _MakeTxn
):
    dbi = make_dbi_with_data([(key, value)])
    txn = make_txn(read_only=True)
    assert dbi.get(key, txn) == value


@pytest.mark.parametrize("key", _key_samples)
def test_get_notfound(key: bytes, make_txn: _MakeTxn):
    txn = make_txn(read_only=True)
    dbi = lmdb_c.LmdbDatabase(txn)
    with pytest.raises(lmdb_c.LmdbException) as e:
        dbi.get(key, txn)
    assert e.value.rc == lmdb_c.MDB_NOTFOUND


@pytest.mark.parametrize("key,value", _key_value_samples)
def test_delete(
    key: bytes, value: bytes, make_dbi_with_data: _MakeDbi, make_txn: _MakeTxn
):
    dbi = make_dbi_with_data([(key, value)])
    txn = make_txn(read_only=False)

    dbi.delete(key, txn)
    txn.commit()

    txn = make_txn(read_only=True)
    with pytest.raises(lmdb_c.LmdbException) as e:
        dbi.get(key, txn)
    assert e.value.rc == lmdb_c.MDB_NOTFOUND


def test_put_multithreading():
    pass


def test_put_multiprocessing():
    pass


def test_get_multithreading():
    pass


def test_get_multiprocessing():
    pass


def test_delete_multithreading():
    pass


def test_delete_multithreading():
    pass
