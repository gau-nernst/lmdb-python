import os
import pickle
import threading
import time
from pathlib import Path
from typing import Callable, Iterable, Tuple

import lmdb_python.types
import pytest
from lmdb_python import lmdb_c

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


def test_env_init(tmp_path: Path):
    lmdb_c.LmdbEnvironment(str(tmp_path))
    assert os.path.isfile(tmp_path / "data.mdb")
    assert os.path.isfile(tmp_path / "lock.mdb")


def test_env_init_no_dir_exception(tmp_path: Path):
    invalid_tmp_path = tmp_path / "invalid"
    with pytest.raises(FileNotFoundError):
        lmdb_c.LmdbEnvironment(str(invalid_tmp_path))


def test_env_init_no_subdir(tmp_path: Path):
    env_path = str(tmp_path / "test_lmdb")
    lmdb_c.LmdbEnvironment(env_path, no_subdir=True)
    assert os.path.isfile(env_path)
    assert os.path.isfile(env_path + "-lock")


def test_env_init_no_lock(tmp_path: Path):
    lmdb_c.LmdbEnvironment(str(tmp_path), no_lock=True)
    assert os.path.isfile(tmp_path / "data.mdb")
    assert not os.path.exists(tmp_path / "lock.mdb")


def test_env_init_read_only(tmp_path: Path):
    # for read-only env, a DB must exist first
    lmdb_c.LmdbEnvironment(str(tmp_path))
    env = lmdb_c.LmdbEnvironment(str(tmp_path), read_only=True)
    assert env.get_flags().read_only
    with pytest.raises((PermissionError, OSError)):
        lmdb_c.LmdbTransaction(env, read_only=False)


@pytest.fixture
def lmdb_env(tmp_path: Path):
    return lmdb_c.LmdbEnvironment(str(tmp_path))


def test_env_get_stat(lmdb_env: lmdb_c.LmdbEnvironment):
    stats = lmdb_env.get_stat()
    assert isinstance(stats, lmdb_python.types.LmdbStat)
    for s in stats:
        assert isinstance(s, int)


def test_env_get_info(lmdb_env: lmdb_c.LmdbEnvironment):
    info = lmdb_env.get_info()
    assert isinstance(info, lmdb_python.types.LmdbEnvInfo)
    for i in info:
        assert isinstance(i, int)


def test_env_get_flags(lmdb_env: lmdb_c.LmdbEnvironment):
    flags = lmdb_env.get_flags()
    assert isinstance(flags, lmdb_python.types.LmdbEnvFlags)
    for f in flags:
        assert isinstance(f, bool)


def test_env_get_path(lmdb_env: lmdb_c.LmdbEnvironment):
    path = lmdb_env.get_path()
    assert isinstance(path, str)
    assert os.path.exists(path)


def test_env_get_fd(lmdb_env: lmdb_c.LmdbEnvironment):
    fd = lmdb_env.get_fd()
    assert isinstance(fd, int)
    os.fdopen(fd)
    # TODO: try to do something with the file obbject


@pytest.mark.parametrize("map_size_mb", (10, 100, 1000))
def test_env_set_map_size(lmdb_env: lmdb_c.LmdbEnvironment, map_size_mb: int):
    new_map_size = map_size_mb * 1024 * 1024
    lmdb_env.set_map_size(new_map_size)
    info = lmdb_env.get_info()
    assert info.me_mapsize == new_map_size


def test_env_get_max_readers(lmdb_env: lmdb_c.LmdbEnvironment):
    max_readers = lmdb_env.get_max_readers()
    assert isinstance(max_readers, int)
    info = lmdb_env.get_info()
    assert info.me_maxreaders == max_readers


def test_env_get_max_key_size(lmdb_env: lmdb_c.LmdbEnvironment):
    max_key_size = lmdb_env.get_max_key_size()
    assert isinstance(max_key_size, int)


@pytest.mark.parametrize("map_size_mb", (10, 100, 1000))
def test_env_init_map_size(tmp_path: Path, map_size_mb: int):
    map_size = map_size_mb * 1024 * 1024
    env = lmdb_c.LmdbEnvironment(str(tmp_path), map_size=map_size)
    info = env.get_info()
    assert info.me_mapsize == map_size


@pytest.mark.parametrize("max_readers", (10, 100))
def test_env_init_max_readers(tmp_path: Path, max_readers: int):
    env = lmdb_c.LmdbEnvironment(str(tmp_path), max_readers=max_readers)
    assert env.get_max_readers() == max_readers

    def target(i):
        if i >= max_readers:
            with pytest.raises(lmdb_c.LmdbException) as e:
                txn = lmdb_c.LmdbTransaction(env, read_only=True)
            assert e.value.rc == lmdb_c.MDB_READERS_FULL
        else:
            txn = lmdb_c.LmdbTransaction(env, read_only=True)
            time.sleep(2)
            txn.abort()

    threads = []
    for i in range(max_readers + 1):
        threads.append(threading.Thread(target=target, args=(i,)))
    for th in threads:
        th.start()
    for th in threads:
        th.join()


def test_env_pickle(lmdb_env: lmdb_c.LmdbEnvironment):
    pickled_data = pickle.dumps(lmdb_env)
    unpickled_env: lmdb_c.LmdbEnvironment = pickle.loads(pickled_data)
    assert unpickled_env is not lmdb_env
    assert unpickled_env.get_path() == lmdb_env.get_path()
    assert unpickled_env.get_info() == lmdb_env.get_info()
    assert unpickled_env.get_stat() == lmdb_env.get_stat()


def test_txn_init(lmdb_env: lmdb_c.LmdbEnvironment):
    lmdb_c.LmdbTransaction(lmdb_env)


def test_txn_init_read_only(lmdb_env: lmdb_c.LmdbEnvironment):
    txn = lmdb_c.LmdbTransaction(lmdb_env, read_only=True)
    dbi = lmdb_c.LmdbDatabase(txn)
    with pytest.raises((PermissionError, OSError)):
        dbi.put(b"key", b"value", txn)
    txn.abort()


@pytest.fixture
def make_txn(lmdb_env: lmdb_c.LmdbEnvironment):
    def _make_txn(read_only: bool) -> lmdb_c.LmdbTransaction:
        return lmdb_c.LmdbTransaction(lmdb_env, read_only=read_only)

    return _make_txn


def test_txn_get_id(make_txn: _MakeTxn):
    txn = make_txn(read_only=False)
    txn_id = txn.get_id()
    assert isinstance(txn_id, int)
    assert txn_id == 1


def test_txn_get_id_invalid(make_txn: _MakeTxn):
    txn = make_txn(read_only=False)
    txn.abort()
    txn_id = txn.get_id()
    assert isinstance(txn_id, int)
    assert txn_id == 0


def test_dbi_init(make_txn: _MakeTxn):
    txn = make_txn(read_only=True)
    lmdb_c.LmdbDatabase(txn)


def test_dbi_init_name(tmp_path):
    env = lmdb_c.LmdbEnvironment(str(tmp_path), max_dbs=1)
    txn = lmdb_c.LmdbTransaction(env, read_only=False)
    lmdb_c.LmdbDatabase(txn, name="database", create=True)
    txn.commit()


def test_dbi_init_name_no_create(tmp_path):
    env = lmdb_c.LmdbEnvironment(str(tmp_path), max_dbs=1)
    txn = lmdb_c.LmdbTransaction(env, read_only=False)

    with pytest.raises(lmdb_c.LmdbException) as e:
        lmdb_c.LmdbDatabase(txn, name="database")
    assert e.value.rc == lmdb_c.MDB_NOTFOUND
    txn.abort()


@pytest.mark.parametrize("max_dbs", (0, 1, 5))
def test_env_init_max_dbs(tmp_path: Path, max_dbs: int):
    env = lmdb_c.LmdbEnvironment(str(tmp_path), max_dbs=max_dbs)
    txn = lmdb_c.LmdbTransaction(env, read_only=False)

    for i in range(max_dbs):
        lmdb_c.LmdbDatabase(txn, name=f"db_{i}", create=True)
    with pytest.raises(lmdb_c.LmdbException) as e:
        lmdb_c.LmdbDatabase(txn, name=f"db_{max_dbs}", create=True)
    assert e.value.rc == lmdb_c.MDB_DBS_FULL
    txn.commit()


_key_samples = (b"key123", "u1234532".encode("utf-8"))
_value_samples = (b"value456", pickle.dumps(["1", 12, "Engineer"]))
_key_value_samples = tuple(zip(_key_samples, _value_samples))


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


def test_dbi_get_stat(make_txn: _MakeTxn):
    txn = make_txn(read_only=False)
    dbi = lmdb_c.LmdbDatabase(txn)
    stat = dbi.get_stat(txn)
    assert isinstance(stat, lmdb_python.types.LmdbStat)
    for s in stat:
        assert isinstance(s, int)


def test_dbi_get_flags(make_txn: _MakeTxn):
    txn = make_txn(read_only=False)
    dbi = lmdb_c.LmdbDatabase(txn)
    flags = dbi.get_flags(txn)
    assert isinstance(flags, lmdb_python.types.LmdbDbFlags)
    for f in flags:
        assert isinstance(f, int)


def test_dbi_empty_db(make_dbi_with_data: _MakeDbi, make_txn: _MakeTxn):
    dbi = make_dbi_with_data([(b"key1", b"value1")])
    txn = make_txn(read_only=True)
    stat = dbi.get_stat(txn)
    txn.abort()
    assert stat.ms_entries == 1

    txn = make_txn(read_only=False)
    dbi.empty_db(txn)
    txn.commit()

    txn = make_txn(read_only=True)
    stat = dbi.get_stat(txn)
    txn.abort()
    assert stat.ms_entries == 0


def test_dbi_delete_db(tmp_path):
    db_name = "database"
    env = lmdb_c.LmdbEnvironment(str(tmp_path), max_dbs=1)
    txn = lmdb_c.LmdbTransaction(env, read_only=False)
    dbi = lmdb_c.LmdbDatabase(txn, name=db_name, create=True)
    txn.commit()

    txn = lmdb_c.LmdbTransaction(env, read_only=False)
    dbi = lmdb_c.LmdbDatabase(txn, name=db_name)
    dbi.delete_db(txn)
    txn.commit()

    txn = lmdb_c.LmdbTransaction(env, read_only=True)
    with pytest.raises(lmdb_c.LmdbException) as e:
        dbi = lmdb_c.LmdbDatabase(txn, name=db_name)
    assert e.value.rc == lmdb_c.MDB_NOTFOUND
    txn.abort()


@pytest.mark.parametrize("key,value", _key_value_samples)
def test_get(
    key: bytes, value: bytes, make_dbi_with_data: _MakeDbi, make_txn: _MakeTxn
):
    dbi = make_dbi_with_data([(key, value)])
    txn = make_txn(read_only=True)
    assert dbi.get(key, txn) == value
    txn.abort()


@pytest.mark.parametrize("key", _key_samples)
def test_get_notfound(key: bytes, make_txn: _MakeTxn):
    txn = make_txn(read_only=True)
    dbi = lmdb_c.LmdbDatabase(txn)
    with pytest.raises(lmdb_c.LmdbException) as e:
        dbi.get(key, txn)
    assert e.value.rc == lmdb_c.MDB_NOTFOUND
    txn.abort()


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
    txn.abort()


def _test_data_is_present(env: lmdb_c.LmdbEnvironment, samples: Iterable[_KeyValue]):
    txn = lmdb_c.LmdbTransaction(env, read_only=True)
    dbi = lmdb_c.LmdbDatabase(txn)
    for k, v in samples:
        assert dbi.get(k, txn) == v


@pytest.mark.parametrize("method", ("copy", "copy2"))
def test_env_copy(
    lmdb_env: lmdb_c.LmdbEnvironment,
    make_dbi_with_data: _MakeDbi,
    tmp_path: Path,
    method: str,
):
    make_dbi_with_data(_key_value_samples)
    copied_path = tmp_path / "new_folder"
    os.makedirs(copied_path)
    getattr(lmdb_env, method)(str(copied_path))
    assert os.path.isfile(copied_path / "data.mdb")

    if os.name != "nt":
        original_size = os.stat(tmp_path / "data.mdb").st_size
        copied_size = os.stat(copied_path / "data.mdb").st_size
        assert original_size == copied_size

    copied_env = lmdb_c.LmdbEnvironment(str(copied_path), read_only=True)
    _test_data_is_present(copied_env, _key_value_samples)


@pytest.mark.parametrize("method", ("copy_fd", "copy_fd2"))
def test_env_copy_fd(
    lmdb_env: lmdb_c.LmdbEnvironment,
    make_dbi_with_data: _MakeDbi,
    tmp_path: Path,
    method: str,
):
    make_dbi_with_data(_key_value_samples)
    copied_path = tmp_path / "copied.mdb"
    with open(copied_path, "wb") as f:
        getattr(lmdb_env, method)(f.fileno())

    if os.name != "nt":
        original_size = os.stat(tmp_path / "data.mdb").st_size
        copied_size = os.stat(copied_path).st_size
        assert original_size == copied_size

    copied_env = lmdb_c.LmdbEnvironment(
        str(copied_path), read_only=True, no_subdir=True
    )
    _test_data_is_present(copied_env, _key_value_samples)


def test_env_copy2_compact(
    lmdb_env: lmdb_c.LmdbEnvironment,
    make_txn: _MakeTxn,
    make_dbi_with_data: _MakeDbi,
    tmp_path: Path,
):
    dbi = make_dbi_with_data(_key_value_samples)
    txn = make_txn(read_only=False)
    for k in _key_samples:
        dbi.delete(k, txn)
    txn.commit()

    copied_path = tmp_path / "new_folder"
    os.makedirs(copied_path)
    lmdb_env.copy2(str(copied_path), compact=True)
    assert os.path.isfile(copied_path / "data.mdb")

    lmdb_c.LmdbEnvironment(str(copied_path), read_only=True)
    original_size = os.stat(tmp_path / "data.mdb").st_size
    copied_size = os.stat(copied_path / "data.mdb").st_size
    assert copied_size < original_size


def test_env_copy_fd2_compact(
    lmdb_env: lmdb_c.LmdbEnvironment,
    make_txn: _MakeTxn,
    make_dbi_with_data: _MakeDbi,
    tmp_path: Path,
):
    dbi = make_dbi_with_data(_key_value_samples)
    txn = make_txn(read_only=False)
    for k in _key_samples:
        dbi.delete(k, txn)
    txn.commit()

    copied_path = tmp_path / "copied.mdb"
    with open(copied_path, "wb") as f:
        lmdb_env.copy_fd2(f.fileno(), compact=True)

    lmdb_c.LmdbEnvironment(str(copied_path), read_only=True, no_subdir=True)
    original_size = os.stat(tmp_path / "data.mdb").st_size
    copied_size = os.stat(copied_path).st_size
    assert copied_size < original_size
