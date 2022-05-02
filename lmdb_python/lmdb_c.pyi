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

class LmdbEnvironment:
    def create_env(self) -> int: ...
    def open_env(
        self, env_name: str, no_subdir: bool = False, read_only: bool = False
    ) -> int: ...
    def close_env(self) -> None: ...

class LmdbTransaction:
    def begin_txn(self, env: LmdbEnvironment, read_only: bool = True) -> int: ...
    def commit_txn(self) -> int: ...
    def abort_txn(self) -> None: ...

class LmdbDatabase:
    def open_dbi(self, txn: LmdbTransaction) -> int: ...

class LmdbValue:
    def __init__(self, data: Optional[bytes]): ...
    def to_bytes(self) -> Optional[bytes]: ...

def put(
    key: LmdbValue, value: LmdbValue, txn: LmdbTransaction, dbi: LmdbDatabase
) -> int: ...
def get(
    key: LmdbValue, value: LmdbValue, txn: LmdbTransaction, dbi: LmdbDatabase
) -> int: ...
def delete(key: LmdbValue, txn: LmdbTransaction, dbi: LmdbDatabase) -> int: ...
