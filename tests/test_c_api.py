import os
import pathlib
import pickle
import random
from typing import Any, Callable, Iterable, Tuple

import lmdb_python.types
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
    assert os.path.isfile(tmp_path / "data.mdb")
    assert os.path.isfile(tmp_path / "lock.mdb")


def test_env_init_no_dir_exception(tmp_path: pathlib.Path):
    invalid_tmp_path = tmp_path / "invalid"
    with pytest.raises(FileNotFoundError):
        lmdb_c.LmdbEnvironment(str(invalid_tmp_path))


def test_env_init_no_subdir(tmp_path: pathlib.Path):
    env_path = str(tmp_path / "test_lmdb")
    lmdb_c.LmdbEnvironment(env_path, no_subdir=True)
    assert os.path.isfile(env_path)
    assert os.path.isfile(env_path + "-lock")


def test_env_init_no_lock(tmp_path: pathlib.Path):
    lmdb_c.LmdbEnvironment(str(tmp_path), no_lock=True)
    assert os.path.isfile(tmp_path / "data.mdb")
    assert not os.path.exists(tmp_path / "lock.mdb")


def test_env_init_read_only(tmp_path: pathlib.Path):
    # for read-only env, an DB must exist first
    # create a db
    lmdb_c.LmdbEnvironment(str(tmp_path))
    env = lmdb_c.LmdbEnvironment(str(tmp_path), read_only=True)
    # TODO: test for read_only
    assert env.get_flags().read_only


@pytest.fixture
def lmdb_env(tmp_path: pathlib.Path):
    return lmdb_c.LmdbEnvironment(str(tmp_path))


def test_env_copy(lmdb_env, tmp_path):
    copied_path = tmp_path / "new_folder"
    os.makedirs(copied_path)
    lmdb_env.copy(str(copied_path))
    assert os.path.isfile(tmp_path / "data.mdb")
    assert os.path.exists(tmp_path / "lock.mdb")


def test_env_copy_fd(lmdb_env, tmp_path):
    copied_path = tmp_path / "copied.mdb"
    f = open(copied_path, "wb")
    lmdb_env.copy_fd(f.fileno())
    f.close()
    lmdb_c.LmdbEnvironment(str(copied_path), read_only=True, no_subdir=True)


def test_env_copy2(lmdb_env, tmp_path):
    copied_path = tmp_path / "new_folder"
    os.makedirs(copied_path)
    lmdb_env.copy2(str(copied_path))
    assert os.path.isfile(tmp_path / "data.mdb")
    assert os.path.exists(tmp_path / "lock.mdb")


def test_env_copy2_compact(lmdb_env, tmp_path):
    copied_path = tmp_path / "new_folder"
    os.makedirs(copied_path)
    lmdb_env.copy2(str(copied_path), compact=True)
    assert os.path.isfile(tmp_path / "data.mdb")
    assert os.path.exists(tmp_path / "lock.mdb")
    # TODO: add some data, remove some data,
    # check the copied file is smaller


def test_env_copy_fd2(lmdb_env, tmp_path):
    copied_path = tmp_path / "copied.mdb"
    f = open(copied_path, "wb")
    lmdb_env.copy_fd2(f.fileno())
    f.close()
    lmdb_c.LmdbEnvironment(str(copied_path), read_only=True, no_subdir=True)


def test_env_copy_fd2_compact(lmdb_env, tmp_path):
    copied_path = tmp_path / "copied.mdb"
    f = open(copied_path, "wb")
    lmdb_env.copy_fd2(f.fileno(), compact=True)
    f.close()
    lmdb_c.LmdbEnvironment(str(copied_path), read_only=True, no_subdir=True)
    # TODO: add some data, remove some data,
    # check the copied file is smaller


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


def test_env_set_map_size(lmdb_env: lmdb_c.LmdbEnvironment):
    new_map_size = random.randint(10, 1000) * 1024 * 1024  # 10MB - 1GB
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
def test_env_init_map_size(tmp_path: pathlib.Path, map_size_mb: int):
    map_size = map_size_mb * 1024 * 1024
    env = lmdb_c.LmdbEnvironment(str(tmp_path), map_size=map_size)
    info = env.get_info()
    assert info.me_mapsize == map_size


@pytest.mark.parametrize("max_readers", (10, 100, 1000))
def test_env_init_max_readers(tmp_path: pathlib.Path, max_readers: int):
    env = lmdb_c.LmdbEnvironment(str(tmp_path), max_readers=max_readers)
    assert env.get_max_readers() == max_readers


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
def test_env_init_max_dbs(tmp_path: pathlib.Path, max_dbs: int):
    env = lmdb_c.LmdbEnvironment(str(tmp_path), max_dbs=max_dbs)
    txn = lmdb_c.LmdbTransaction(env, read_only=False)

    for i in range(max_dbs):
        lmdb_c.LmdbDatabase(txn, name=f"db_{i}", create=True)
    with pytest.raises(lmdb_c.LmdbException) as e:
        lmdb_c.LmdbDatabase(txn, name=f"db_{max_dbs}", create=True)
    assert e.value.rc == lmdb_c.MDB_DBS_FULL
    txn.commit()


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
