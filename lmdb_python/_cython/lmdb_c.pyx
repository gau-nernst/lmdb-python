from typing import Optional, Dict
from collections import namedtuple

cimport lmdb_python._cython.lmdb as lmdb


MDB_VERSION_MAJOR = lmdb.MDB_VERSION_MAJOR
MDB_VERSION_MINOR = lmdb.MDB_VERSION_MINOR
MDB_VERSION_PATCH = lmdb.MDB_VERSION_PATCH

MDB_KEYEXIST = lmdb.MDB_KEYEXIST
MDB_NOTFOUND = lmdb.MDB_NOTFOUND
MDB_PAGE_NOTFOUND = lmdb.MDB_PAGE_NOTFOUND
MDB_CORRUPTED = lmdb.MDB_CORRUPTED
MDB_PANIC = lmdb.MDB_PANIC
MDB_VERSION_MISMATCH = lmdb.MDB_VERSION_MISMATCH
MDB_INVALID = lmdb.MDB_INVALID
MDB_MAP_FULL = lmdb.MDB_MAP_FULL
MDB_DBS_FULL = lmdb.MDB_DBS_FULL
MDB_READERS_FULL = lmdb.MDB_READERS_FULL
MDB_TLS_FULL = lmdb.MDB_TLS_FULL
MDB_TXN_FULL = lmdb.MDB_TXN_FULL
MDB_CURSOR_FULL = lmdb.MDB_CURSOR_FULL
MDB_PAGE_FULL = lmdb.MDB_PAGE_FULL
MDB_MAP_RESIZED = lmdb.MDB_MAP_RESIZED
MDB_INCOMPATIBLE = lmdb.MDB_INCOMPATIBLE
MDB_BAD_RSLOT = lmdb.MDB_BAD_RSLOT
MDB_BAD_TXN = lmdb.MDB_BAD_TXN
MDB_BAD_VALSIZE = lmdb.MDB_BAD_VALSIZE
MDB_BAD_DBI = lmdb.MDB_BAD_DBI


def strerror(err: int) -> str:
    return lmdb.mdb_strerror(err).decode()


class LmdbException(Exception):
    def __init__(self, rc: int):
        self.rc = rc
        msg = f"{strerror(rc)}. Code {rc}"
        super().__init__(msg)


def _check_rc(rc: int) -> None:
    if rc != 0:
        raise LmdbException(rc)


cdef class LmdbEnvironment:
    cdef lmdb.MDB_env* env

    def __cinit__(self, env_name: str, no_subdir: bool = False, read_only: bool = False):
        rc = lmdb.mdb_env_create(&self.env)
        _check_rc(rc)
        
        env_flags = 0
        if no_subdir:
            env_flags |= lmdb.MDB_NOSUBDIR
        if read_only:
            env_flags |= lmdb.MDB_RDONLY
        
        rc = lmdb.mdb_env_open(self.env, env_name.encode("utf-8"), env_flags, 0664)
        _check_rc(rc)

    def stat(self) -> int:
        cdef lmdb.MDB_stat stat
        rc = lmdb.mdb_env_stat(self.env, &stat)
        _check_rc(rc)
        return _LmdbStat(
            stat.ms_psize,
            stat.ms_depth,
            stat.ms_branch_pages,
            stat.ms_leaf_pages,
            stat.ms_overflow_pages,
            stat.ms_entries
        )

    # def create_env(self) -> None:
    #     rc = lmdb.mdb_env_create(&self.env)
    #     _check_rc(rc)
    
    # def open_env(self, env_name: str, no_subdir: bool = False, read_only: bool = False) -> None:
    #     env_flags = 0
    #     if no_subdir:
    #         env_flags |= lmdb.MDB_NOSUBDIR
    #     if read_only:
    #         env_flags |= lmdb.MDB_RDONLY
    #     rc = lmdb.mdb_env_open(self.env, env_name.encode("utf-8"), env_flags, 0664)
    #     _check_rc(rc)

    # def close_env(self) -> None:
    #     lmdb.mdb_env_close(self.env)

    # def __dealloc__(self):
    #     lmdb.mdb_env_close(self.env)


cdef class LmdbTransaction:
    cdef lmdb.MDB_txn* txn
    env: LmdbEnvironment

    def __cinit__(self, env: LmdbEnvironment, read_only: bool = True):
        self.env = env      # add internal reference so it won't be garbage-collected
        rc = lmdb.mdb_txn_begin(env.env, NULL, lmdb.MDB_RDONLY if read_only else 0, &self.txn)
        _check_rc(rc)
    
    def commit(self) -> None:
        rc = lmdb.mdb_txn_commit(self.txn)
        _check_rc(rc)

    def abort(self) -> None:
        lmdb.mdb_txn_abort(self.txn)
    
    # def __dealloc__(self):
    #     lmdb.mdb_txn_abort(self.txn)


cdef class _LmdbData:
    cdef lmdb.MDB_val data

    def __cinit__(self, data: Optional[bytes] = None):
        if data is not None:
            self.data.mv_size = len(data)
            self.data.mv_data = <char*> data

    def to_bytes(self) -> Optional[bytes]:
        if self.data.mv_data == NULL:
            return None
        return (<char*> self.data.mv_data)[:self.data.mv_size]

    def __repr__(self) -> str:
        return f"_LmdbValue({self.to_bytes()})"


cdef class LmdbDatabase:
    cdef lmdb.MDB_dbi dbi

    def __cinit__(self, txn: LmdbTransaction) -> int:
        rc = lmdb.mdb_dbi_open(txn.txn, NULL, 0, &self.dbi)
        _check_rc(rc)

    def put(self, key: bytes, value: bytes, txn: LmdbTransaction) -> None:
        _key = _LmdbData(key)
        _value = _LmdbData(value)

        rc = lmdb.mdb_put(txn.txn, self.dbi, &_key.data, &_value.data, 0)
        _check_rc(rc)

    def get(self, key: bytes, txn: LmdbTransaction) -> bytes:
        _key = _LmdbData(key)
        _value = _LmdbData()

        rc = lmdb.mdb_get(txn.txn, self.dbi, &_key.data, &_value.data)
        _check_rc(rc)

        return _value.to_bytes()

    def delete(self, key: bytes, txn: LmdbTransaction) -> None:
        _key = _LmdbData(key)

        rc = lmdb.mdb_del(txn.txn, self.dbi, &_key.data, NULL)
        _check_rc(rc)


_LmdbStat = namedtuple(
    "_LmdbStat", [
        "ms_psize",
        "ms_depth",
        "ms_branch_pages",
        "ms_leaf_pages",
        "ms_overflow_pages",
        "ms_entries"
    ]
)

cdef class LmdbStat:
    cdef lmdb.MDB_stat stat

    @property
    def ms_psize(self) -> int:
        return self.stat.ms_psize

    @property
    def ms_depth(self) -> int:
        return self.stat.ms_depth

    @property
    def ms_branch_pages(self) -> int:
        return self.stat.ms_branch_pages

    @property
    def ms_leaf_pages(self) -> int:
        return self.stat.ms_leaf_pages

    @property
    def ms_overflow_pages(self) -> int:
        return self.stat.ms_overflow_pages

    @property
    def ms_entries(self) -> int:
        return self.stat.ms_entries

    def to_dict(self) -> Dict[str, int]:
        return {
            "ms_psize": self.ms_psize,
            "ms_depth": self.ms_depth,
            "ms_branch_pages": self.ms_branch_pages,
            "ms_leaf_pages": self.ms_leaf_pages,
            "ms_overflow_pages": self.ms_overflow_pages,
            "ms_entries": self.ms_entries
        }


cdef class LmdbEnvInfo:
    cdef lmdb.MDB_envinfo envinfo

    @property
    def me_mapsize(self) -> int: 
        return self.envinfo.me_mapsize

    @property
    def me_last_pgno(self) -> int: 
        return self.envinfo.me_last_pgno

    @property
    def me_last_txnid(self) -> int: 
        return self.envinfo.me_last_txnid

    @property
    def me_maxreaders(self) -> int: 
        return self.envinfo.me_maxreaders

    @property
    def me_numreaders(self) -> int: 
        return self.envinfo.me_numreaders

    def to_dict(self) -> Dict[str, int]:
        return {
            "me_mapsize": self.me_mapsize,
            "me_last_pgno": self.me_last_pgno,
            "me_last_txnid": self.me_last_txnid,
            "me_maxreaders": self.me_maxreaders,
            "me_numreaders": self.me_numreaders
        }


def env_info(env: LmdbEnvironment, envinfo: LmdbEnvInfo) -> int:
    return lmdb.mdb_env_info(env.env, &envinfo.envinfo)
