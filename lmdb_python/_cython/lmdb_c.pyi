from typing import Optional

from ..types import LmdbDbFlags, LmdbEnvFlags, LmdbEnvInfo, LmdbStat

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

def version() -> str: ...
def strerror(err: int) -> str: ...

class LmdbException(Exception):
    rc: int

class LmdbEnvironment:
    def __init__(
        self,
        path: str,
        map_size: int = 10 * 1024 * 1024,
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
    ): ...
    def copy(self, path: str) -> None: ...
    def copy_fd(self, fd: int) -> None: ...
    def copy2(self, path: str, compact: bool = False) -> None: ...
    def copy_fd2(self, fd: int, compact: bool = False) -> None: ...
    def get_stat(self) -> LmdbStat: ...
    def get_info(self) -> LmdbEnvInfo: ...
    def sync(self, force: bool) -> None: ...
    def close(self) -> None: ...
    def set_flags(
        self,
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
        unset: bool = False,
    ) -> None: ...
    def get_flags(self) -> LmdbEnvFlags: ...
    def get_path(self) -> str: ...
    def get_fd(self) -> int: ...
    def set_map_size(self, size: int) -> None: ...
    def get_max_readers(self) -> int: ...
    def get_max_key_size(self) -> int: ...

class LmdbTransaction:
    def __init__(self, env: LmdbEnvironment, read_only: bool = False): ...
    def get_id(self) -> int: ...
    def commit(self) -> None: ...
    def abort(self) -> None: ...

class _LmdbData:
    def __init__(self, data: Optional[bytes]): ...
    def to_bytes(self) -> Optional[bytes]: ...

class LmdbDatabase:
    def __init__(
        self,
        txn: LmdbTransaction,
        name: Optional[str] = None,
        reverse_key: bool = False,
        duplicate_sort: bool = False,
        integer_key: bool = False,
        duplicate_fixed: bool = False,
        integer_duplicate: bool = False,
        reverse_duplicate: bool = False,
        create: bool = False,
    ): ...
    def get_stat(self, txn: LmdbTransaction) -> LmdbStat: ...
    def get_flags(self, txn: LmdbTransaction) -> LmdbDbFlags: ...
    def empty_db(self, txn: LmdbTransaction) -> None: ...
    def delete_db(self, txn: LmdbTransaction) -> None: ...
    def get(self, key: bytes, txn: LmdbTransaction) -> bytes: ...
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
    ) -> None: ...
    def delete(self, key: bytes, txn: LmdbTransaction) -> None: ...
