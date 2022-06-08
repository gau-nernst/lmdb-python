import os
from typing import Generator, Iterable, Optional, Tuple

from ._cython.lmdb_c import LmdbDatabase, LmdbEnvironment, LmdbTransaction
from .types import LmdbEnvFlags

__all__ = ["Database"]


class Database:
    def __init__(
        self,
        path: str,
        map_size: int = 10 * 1024 * 1024,  # 10MB
        max_readers: int = 126,
        max_dbs: int = 0,
        flags: Optional[LmdbEnvFlags] = None,
    ):
        if flags is None:
            flags = LmdbEnvFlags()
        if not flags.no_subdir and not os.path.exists(path):
            os.makedirs(path)
        self.env = LmdbEnvironment(path, map_size, max_readers, max_dbs, *flags)
        with LmdbTransaction(self.env, read_only=flags.read_only) as txn:
            self.dbi = LmdbDatabase(txn)

    def __getstate__(self) -> LmdbEnvironment:
        return self.env

    def __setstate__(self, state: LmdbEnvironment):
        self.env = state
        with LmdbTransaction(self.env, read_only=self.env.get_flags().read_only) as txn:
            self.dbi = LmdbDatabase(txn)

    def get(self, key: bytes) -> bytes:
        with LmdbTransaction(self.env, read_only=True) as txn:
            return self.dbi.get(key, txn)

    def put(self, key: bytes, value: bytes) -> None:
        with LmdbTransaction(self.env) as txn:
            self.dbi.put(key, value, txn)

    def delete(self, key: bytes) -> None:
        with LmdbTransaction(self.env) as txn:
            self.dbi.delete(key, txn)

    def get_batch(self, keys: Iterable[bytes]) -> Generator[bytes, None, None]:
        with LmdbTransaction(self.env, read_only=True) as txn:
            for k in keys:
                yield self.dbi.get(k, txn)

    def put_batch(self, kv_pairs: Iterable[Tuple[bytes, bytes]]) -> None:
        with LmdbTransaction(self.env) as txn:
            for k, v in kv_pairs:
                self.dbi.put(k, v, txn)

    def delete_batch(self, keys: Iterable[bytes]) -> None:
        with LmdbTransaction(self.env) as txn:
            for k in keys:
                self.dbi.delete(k, txn)
