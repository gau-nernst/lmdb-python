from ._cython import lmdb_c

__lmdb_version__ = lmdb_c.version()
__version__ = "0.0.1"
