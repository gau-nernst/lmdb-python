from . import lmdb_c, errors


def get_lmdb_version() -> str:
    return f"{lmdb_c.MDB_VERSION_MAJOR}.{lmdb_c.MDB_VERSION_MINOR}.{lmdb_c.MDB_VERSION_PATCH}"
