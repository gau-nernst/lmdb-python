import os
from typing import Iterable, Tuple

from ._cython import lmdb_c

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
    def __init__(self, path: str, read_only: bool = False, **kwargs):
        if not os.path.exists(path):
            os.makedirs(path)
        self.env = lmdb_c.LmdbEnvironment(path, read_only=read_only, **kwargs)
        with _Transaction(self.env, read_only=read_only) as txn:
            self.dbi = lmdb_c.LmdbDatabase(txn)

    def get(self, key: bytes):
        with _Transaction(self.env, read_only=True) as txn:
            return self.dbi.get(key, txn)

    def put(self, key: bytes, value: bytes):
        with _Transaction(self.env) as txn:
            return self.dbi.put(key, value, txn)

    def delete(self, key: bytes):
        with _Transaction(self.env) as txn:
            return self.dbi.delete(key, txn)

    def get_batch(self, keys: Iterable[bytes]):
        with _Transaction(self.env, read_only=True) as txn:
            for k in keys:
                yield self.dbi.get(k, txn)

    def put_batch(self, kv_pairs: Iterable[Tuple[bytes, bytes]]):
        with _Transaction(self.env) as txn:
            for k, v in kv_pairs:
                self.dbi.put(k, v, txn)

    def delete_batch(self, keys: Iterable[bytes]):
        with _Transaction(self.env) as txn:
            for k in keys:
                self.dbi.delete(k, txn)
