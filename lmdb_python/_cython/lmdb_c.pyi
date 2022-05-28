from collections import namedtuple
from typing import Optional

MDB_VERSION_MAJOR: int
MDB_VERSION_MINOR: int
MDB_VERSION_PATCH: int

MDB_KEYEXIST: int
MDB_NOTFOUND: int
MDB_PAGE_NOTFOUND: int
MDB_CORRUPTED: int
MDB_PANIC: int
MDB_VERSION_MISMATCH: int
MDB_INVALID: int
MDB_MAP_FULL: int
MDB_DBS_FULL: int
MDB_READERS_FULL: int
MDB_TLS_FULL: int
MDB_TXN_FULL: int
MDB_CURSOR_FULL: int
MDB_PAGE_FULL: int
MDB_MAP_RESIZED: int
MDB_INCOMPATIBLE: int
MDB_BAD_RSLOT: int
MDB_BAD_TXN: int
MDB_BAD_VALSIZE: int
MDB_BAD_DBI: int

_LmdbStat = namedtuple(
    "_LmdbStat",
    [
        "ms_psize",
        "ms_depth",
        "ms_branch_pages",
        "ms_leaf_pages",
        "ms_overflow_pages",
        "ms_entries",
    ],
)

_LmdbEnvInfo = namedtuple(
    "_LmdbEnvInfo",
    [
        "me_mapsize",
        "me_last_pgno",
        "me_last_txnid",
        "me_maxreaders",
        "me_numreaders",
    ],
)

def strerror(err: int) -> str: ...

class LmdbException(Exception):
    rc: int

class LmdbEnvironment:
    def __init__(
        self, env_name: str, no_subdir: bool = False, read_only: bool = False
    ): ...
    def get_stat(self) -> _LmdbStat: ...
    def get_info(self) -> _LmdbEnvInfo: ...
    def close(self) -> None: ...

class LmdbTransaction:
    def __init__(self, env: LmdbEnvironment, read_only: bool = True): ...
    def commit(self) -> None: ...
    def abort(self) -> None: ...

class _LmdbData:
    def __init__(self, data: Optional[bytes]): ...
    def to_bytes(self) -> Optional[bytes]: ...

class LmdbDatabase:
    def __init__(self, txn: LmdbTransaction): ...
    def put(self, key: bytes, value: bytes, txn: LmdbTransaction) -> None: ...
    def get(self, key: bytes, txn: LmdbTransaction) -> bytes: ...
    def delete(self, key: bytes, txn: LmdbTransaction) -> None: ...
