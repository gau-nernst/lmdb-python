import os
from typing import Generator, Iterable, Optional, Tuple

from ._cython import lmdb_c
from .types import LmdbEnvFlags

__all__ = ["Database"]


class _Transaction:
    def __init__(self, env: lmdb_c.LmdbEnvironment, read_only: bool = False):
        self.read_only = read_only
        self.txn = lmdb_c.LmdbTransaction(env, read_only=read_only)

    def __enter__(self):
        return self.txn

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.read_only:
            self.txn.abort()
        else:
            self.txn.commit()


class Database:
    def __init__(
        self,
        path: str,
        map_size: int = 10 * 1024 * 1024,  # 10MB
        max_readers: int = 126,
        max_dbs: int = 0,
        flags: Optional[LmdbEnvFlags] = None,
    ):
        if not os.path.exists(path):
            os.makedirs(path)
        if flags is None:
            flags = LmdbEnvFlags()
        self.env = lmdb_c.LmdbEnvironment(path, map_size, max_readers, max_dbs, *flags)
        with _Transaction(self.env, read_only=flags.read_only) as txn:
            self.dbi = lmdb_c.LmdbDatabase(txn)
        self.path = path
        self.map_size = map_size
        self.max_readers = max_readers
        self.max_dbs = max_dbs
        self.flags = flags

    def __reduce__(self):
        attrs = (self.path, self.map_size, self.max_readers, self.max_dbs, self.flags)
        return (self.__class__, attrs)

    def get(self, key: bytes) -> bytes:
        with _Transaction(self.env, read_only=True) as txn:
            return self.dbi.get(key, txn)

    def put(self, key: bytes, value: bytes) -> None:
        with _Transaction(self.env) as txn:
            self.dbi.put(key, value, txn)

    def delete(self, key: bytes) -> None:
        with _Transaction(self.env) as txn:
            self.dbi.delete(key, txn)

    def get_batch(self, keys: Iterable[bytes]) -> Generator[bytes, None, None]:
        with _Transaction(self.env, read_only=True) as txn:
            for k in keys:
                yield self.dbi.get(k, txn)

    def put_batch(self, kv_pairs: Iterable[Tuple[bytes, bytes]]) -> None:
        with _Transaction(self.env) as txn:
            for k, v in kv_pairs:
                self.dbi.put(k, v, txn)

    def delete_batch(self, keys: Iterable[bytes]) -> None:
        with _Transaction(self.env) as txn:
            for k in keys:
                self.dbi.delete(k, txn)
