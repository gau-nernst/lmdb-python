import ctypes
import errno
import os
from typing import Optional

from . cimport lmdb
IF UNAME_SYSNAME != "Linux" and UNAME_SYSNAME != "Darwin":
    from . cimport msvcrt
from ..types import LmdbStat, LmdbEnvInfo, LmdbEnvFlags, LmdbDbFlags

# define symbols
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


def version() -> str:
    return lmdb.mdb_version(NULL, NULL, NULL).decode()


def strerror(err: int) -> str:
    return lmdb.mdb_strerror(err).decode()


def _flag_is_set(unsigned int flags, unsigned int flag) -> bool:
    return (flags & flag) == flag


cdef inline lmdb.mdb_filehandle_t _fd_to_handle(int fd):
    IF UNAME_SYSNAME == "Linux" or UNAME_SYSNAME == "Darwin":
        return fd
    ELSE:
        return <lmdb.mdb_filehandle_t>msvcrt._get_osfhandle(fd)


cdef inline int _handle_to_fd(lmdb.mdb_filehandle_t handle):
    IF UNAME_SYSNAME == "Linux" or UNAME_SYSNAME == "Darwin":
        return handle
    ELSE:
        return msvcrt._open_osfhandle(<msvcrt.intptr_t>handle, 0)


class LmdbException(Exception):
    def __init__(self, rc: int):
        self.rc = rc
        msg = f"{strerror(rc)}. Code {rc}"
        super().__init__(msg)


def _check_rc(rc: int) -> None:
    if rc == 0:
        return
    if rc > 0:
        IF UNAME_SYSNAME != "Linux" and UNAME_SYSNAME != "Darwin":
            raise ctypes.WinError(rc)
        ELSE:
            raise OSError(rc, os.strerror(rc))
    raise LmdbException(rc)


cdef class LmdbEnvironment:
    cdef lmdb.MDB_env* env

    def __cinit__(
        self,
        path: str,
        map_size: int = 10 * 1024 * 1024,   # 10MB
        max_readers: int = 126,
        max_dbs: int = 0,
        fixed_map: bool = False,
        no_subdir: bool = False,
        no_sync: bool = False,
        read_only: bool = False,
        no_meta_sync: bool = False,
        write_map: bool = False,
        map_async: bool = False,
        no_tls: bool = False,
        no_lock: bool = False,
        no_readahead: bool = False,
        no_meminit: bool = False,
    ):
        rc = lmdb.mdb_env_create(&self.env)
        if rc:
            self.close()
            _check_rc(rc)

        self.set_map_size(map_size)

        # This function may only be called after
        # mdb_env_create() and before mdb_env_open()
        rc = lmdb.mdb_env_set_maxreaders(self.env, max_readers)
        _check_rc(rc)
        if max_dbs > 0:
            rc = lmdb.mdb_env_set_maxdbs(self.env, max_dbs)
            _check_rc(rc)

        cdef unsigned int flags = 0
        if fixed_map:
            flags |= lmdb.MDB_FIXEDMAP
        if no_subdir:
            flags |= lmdb.MDB_NOSUBDIR
        if no_sync:
            flags |= lmdb.MDB_NOSYNC
        if read_only:
            flags |= lmdb.MDB_RDONLY
        if no_meta_sync:
            flags |= lmdb.MDB_NOMETASYNC
        if write_map:
            flags |= lmdb.MDB_WRITEMAP
        if map_async:
            flags |= lmdb.MDB_MAPASYNC
        if no_tls:
            flags |= lmdb.MDB_NOTLS
        if no_lock:
            flags |= lmdb.MDB_NOLOCK
        if no_readahead:
            flags |= lmdb.MDB_NORDAHEAD
        if no_meminit:
            flags |= lmdb.MDB_NOMEMINIT

        rc = lmdb.mdb_env_open(self.env, path.encode(), flags, 0664)
        if rc:
            self.close()
            _check_rc(rc)

    def copy(self, path: str) -> None:
        rc = lmdb.mdb_env_copy(self.env, path.encode())
        _check_rc(rc)

    def copy_fd(self, fd: int) -> None:
        rc = lmdb.mdb_env_copyfd(self.env, _fd_to_handle(fd))
        _check_rc(rc)

    def copy2(self, path: str, compact: bool = False) -> None:
        cdef unsigned int flags = lmdb.MDB_CP_COMPACT if compact else 0
        rc = lmdb.mdb_env_copy2(self.env, path.encode(), flags)
        _check_rc(rc)
    
    def copy_fd2(self, fd: int, compact: bool = False) -> None:
        cdef unsigned int flags = lmdb.MDB_CP_COMPACT if compact else 0
        rc = lmdb.mdb_env_copyfd2(self.env, _fd_to_handle(fd), flags)
        _check_rc(rc)

    def get_stat(self) -> LmdbStat:
        cdef lmdb.MDB_stat stat
        rc = lmdb.mdb_env_stat(self.env, &stat)
        _check_rc(rc)
        return LmdbStat(
            stat.ms_psize,
            stat.ms_depth,
            stat.ms_branch_pages,
            stat.ms_leaf_pages,
            stat.ms_overflow_pages,
            stat.ms_entries,
        )

    def get_info(self) -> LmdbEnvInfo:
        cdef lmdb.MDB_envinfo envinfo
        rc = lmdb.mdb_env_info(self.env, &envinfo)
        _check_rc(rc)
        return LmdbEnvInfo(
            envinfo.me_mapsize,
            envinfo.me_last_pgno,
            envinfo.me_last_txnid,
            envinfo.me_maxreaders,
            envinfo.me_numreaders,
        )

    def sync(self, force: bool) -> None:
        rc = lmdb.mdb_env_sync(self.env, 1 if force else 0)
        _check_rc(rc)

    def close(self) -> None:
        if self.env is not NULL:
            lmdb.mdb_env_close(self.env)
            self.env = NULL

    def set_flags(
        self,
        no_sync: bool = False,
        no_meta_sync: bool = False,
        map_async: bool = False,
        no_meminit: bool = False,
        unset: bool = False,
    ) -> None:
        cdef unsigned int flags = 0
        if no_sync:
            flags |= lmdb.MDB_NOSYNC
        if no_meta_sync:
            flags |= lmdb.MDB_NOMETASYNC
        if map_async:
            flags |= lmdb.MDB_MAPASYNC
        if no_meminit:
            flags |= lmdb.MDB_NOMEMINIT
        cdef int onoff = 0 if unset else 1
        rc = lmdb.mdb_env_set_flags(self.env, flags, onoff)
        _check_rc(rc)

    def get_flags(self) -> LmdbEnvFlags:
        cdef unsigned int flags
        rc = lmdb.mdb_env_get_flags(self.env, &flags)
        _check_rc(rc)
        return LmdbEnvFlags(
            _flag_is_set(flags, lmdb.MDB_FIXEDMAP),
            _flag_is_set(flags, lmdb.MDB_NOSUBDIR),
            _flag_is_set(flags, lmdb.MDB_NOSYNC),
            _flag_is_set(flags, lmdb.MDB_RDONLY),
            _flag_is_set(flags, lmdb.MDB_NOMETASYNC),
            _flag_is_set(flags, lmdb.MDB_WRITEMAP),
            _flag_is_set(flags, lmdb.MDB_MAPASYNC),
            _flag_is_set(flags, lmdb.MDB_NOTLS),
            _flag_is_set(flags, lmdb.MDB_NOLOCK),
            _flag_is_set(flags, lmdb.MDB_NORDAHEAD),
            _flag_is_set(flags, lmdb.MDB_NOMEMINIT),
        )

    def get_path(self) -> str:
        cdef char* path
        rc = lmdb.mdb_env_get_path(self.env, &path)
        _check_rc(rc)
        py_path = path
        return py_path.decode()
    
    def get_fd(self) -> int:
        cdef lmdb.mdb_filehandle_t fd
        rc = lmdb.mdb_env_get_fd(self.env, &fd)
        _check_rc(rc)
        return _handle_to_fd(fd)

    def set_map_size(self, size: int) -> None:
        rc = lmdb.mdb_env_set_mapsize(self.env, size)
        _check_rc(rc)

    def get_max_readers(self) -> int:
        cdef unsigned int readers
        rc = lmdb.mdb_env_get_maxreaders(self.env, &readers)
        _check_rc(rc)
        return readers

    def get_max_key_size(self) -> int:
        return lmdb.mdb_env_get_maxkeysize(self.env)

    def __dealloc__(self):
        if self.env is not NULL:
            lmdb.mdb_env_close(self.env)
            self.env = NULL


cdef class LmdbTransaction:
    cdef lmdb.MDB_txn* txn
    read_only: bool

    def __cinit__(self, env: LmdbEnvironment, read_only: bool = False):
        self.read_only = read_only
        cdef unsigned int flags = lmdb.MDB_RDONLY if read_only else 0
        rc = lmdb.mdb_txn_begin(env.env, NULL, flags, &self.txn)
        if rc:
            self.abort()
            _check_rc(rc)

    def get_id(self) -> int:
        return lmdb.mdb_txn_id(self.txn)

    def commit(self) -> None:
        if self.txn is not NULL:
            rc = lmdb.mdb_txn_commit(self.txn)
            self.txn = NULL
            _check_rc(rc)

    def abort(self) -> None:
        if self.txn is not NULL:
            lmdb.mdb_txn_abort(self.txn)
            self.txn = NULL

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        if self.read_only:
            self.abort()
        else:
            self.commit()

    def __dealloc__(self) -> None:
        if self.txn is not NULL:
            lmdb.mdb_txn_abort(self.txn)
            self.txn = NULL


cdef lmdb.MDB_val _bytes_to_mv(bytes data):
    cdef lmdb.MDB_val mdb_data
    mdb_data.mv_size = len(data)
    mdb_data.mv_data = <char*> data
    return mdb_data


cdef bytes _mv_to_bytes(lmdb.MDB_val mdb_data):
    return (<char*>mdb_data.mv_data)[:mdb_data.mv_size]


cdef class LmdbDatabase:
    cdef lmdb.MDB_dbi dbi

    def __cinit__(
        self,
        txn: LmdbTransaction,
        name: Optional[str] = None,
        reverse_key: bool = False,
        duplicate_sort: bool = False,
        integer_key: bool = False,
        duplicate_fixed: bool = False,
        integer_duplicate: bool = False,
        reverse_duplicate: bool = False,
        create: bool = False
    ):
        cdef char* c_name = NULL
        if name is not None:
            name_bytes = name.encode()
            c_name = name_bytes
        cdef unsigned int flags = 0
        if reverse_key:
            flags |= lmdb.MDB_REVERSEKEY
        if duplicate_sort:
            flags |= lmdb.MDB_DUPSORT
        if integer_key:
            flags |= lmdb.MDB_INTEGERKEY
        if duplicate_fixed:
            flags |= lmdb.MDB_DUPFIXED
        if integer_duplicate:
            flags |= lmdb.MDB_INTEGERDUP
        if reverse_duplicate:
            flags |= lmdb.MDB_REVERSEDUP
        if create:
            flags |= lmdb.MDB_CREATE
        rc = lmdb.mdb_dbi_open(txn.txn, c_name, flags, &self.dbi)
        _check_rc(rc)

    def get_stat(self, txn: LmdbTransaction) -> LmdbStat:
        cdef lmdb.MDB_stat stat
        rc = lmdb.mdb_stat(txn.txn, self.dbi, &stat)
        _check_rc(rc)
        return LmdbStat(
            stat.ms_psize,
            stat.ms_depth,
            stat.ms_branch_pages,
            stat.ms_leaf_pages,
            stat.ms_overflow_pages,
            stat.ms_entries,
        )

    def get_flags(self, txn: LmdbTransaction) -> int:
        cdef unsigned int flags
        rc = lmdb.mdb_dbi_flags(txn.txn, self.dbi, &flags)
        return LmdbDbFlags(
            _flag_is_set(flags, lmdb.MDB_REVERSEKEY),
            _flag_is_set(flags, lmdb.MDB_DUPSORT),
            _flag_is_set(flags, lmdb.MDB_INTEGERKEY),
            _flag_is_set(flags, lmdb.MDB_DUPFIXED),
            _flag_is_set(flags, lmdb.MDB_INTEGERDUP),
            _flag_is_set(flags, lmdb.MDB_REVERSEDUP),
            _flag_is_set(flags, lmdb.MDB_CREATE),
        )

    def empty_db(self, txn: LmdbTransaction) -> None:
        rc = lmdb.mdb_drop(txn.txn, self.dbi, 0)
        _check_rc(rc)
    
    def delete_db(self, txn: LmdbTransaction) -> None:
        rc = lmdb.mdb_drop(txn.txn, self.dbi, 1)
        _check_rc(rc)

    def get(self, key: bytes, txn: LmdbTransaction) -> bytes:
        cdef lmdb.MDB_val mdb_key = _bytes_to_mv(key)
        cdef lmdb.MDB_val mdb_value
        rc = lmdb.mdb_get(txn.txn, self.dbi, &mdb_key, &mdb_value)
        _check_rc(rc)
        return _mv_to_bytes(mdb_value)
    
    def put(
        self,
        key: bytes,
        value: bytes,
        txn: LmdbTransaction,
        no_overwrite: bool = False,
        no_duplicate: bool = False,
        current: bool = False,
        reserve: bool = False,
        append: bool = False,
        append_duplicate: bool = False,
        multiple: bool = False,
    ) -> None:
        cdef lmdb.MDB_val mdb_key = _bytes_to_mv(key)
        cdef lmdb.MDB_val mdb_value = _bytes_to_mv(value)
        cdef unsigned int flags = 0
        if no_overwrite:
            flags |= lmdb.MDB_NOOVERWRITE
        if no_duplicate:
            flags |= lmdb.MDB_NODUPDATA
        if current:
            flags |= lmdb.MDB_CURRENT
        if reserve:
            flags |= lmdb.MDB_RESERVE
        if append:
            flags |= lmdb.MDB_APPEND
        if append_duplicate:
            flags |= lmdb.MDB_APPENDDUP
        if multiple:
            flags |= lmdb.MDB_MULTIPLE
        rc = lmdb.mdb_put(txn.txn, self.dbi, &mdb_key, &mdb_value, flags)
        _check_rc(rc)

    def delete(self, key: bytes, txn: LmdbTransaction) -> None:
        cdef lmdb.MDB_val mdb_key = _bytes_to_mv(key)
        rc = lmdb.mdb_del(txn.txn, self.dbi, &mdb_key, NULL)
        _check_rc(rc)
