from . import lmdb_c


class LmdbException(Exception):
    def __init__(self, rc: int, msg: str):
        self.rc = rc
        super().__init__(f"{msg}. Return code {rc}")


lmdb_error_code_lookup = {
    lmdb_c.MDB_KEYEXIST: "key/data pair already exists",
    lmdb_c.MDB_NOTFOUND: "key/data pair not found (EOF)",
    lmdb_c.MDB_PAGE_NOTFOUND: "Requested page not found - this usually indicates corruption",
    lmdb_c.MDB_CORRUPTED: "Located page was wrong type",
    lmdb_c.MDB_PANIC: "Update of meta page failed or environment had fatal error",
    lmdb_c.MDB_VERSION_MISMATCH: "Environment version mismatch",
    lmdb_c.MDB_INVALID: "File is not a valid LMDB file",
    lmdb_c.MDB_MAP_FULL: "Environment mapsize reached",
    lmdb_c.MDB_DBS_FULL: "Environment maxdbs reached",
    lmdb_c.MDB_READERS_FULL: "Environment maxreaders reached",
    lmdb_c.MDB_TLS_FULL: "Too many TLS keys in use - Windows only",
    lmdb_c.MDB_TXN_FULL: "Txn has too many dirty pages",
    lmdb_c.MDB_CURSOR_FULL: "Cursor stack too deep - internal error",
    lmdb_c.MDB_PAGE_FULL: "Page has not enough space - internal error",
    lmdb_c.MDB_MAP_RESIZED: "Database contents grew beyond environment mapsize",
    lmdb_c.MDB_INCOMPATIBLE: "Operation and DB incompatible, or DB type changed",
    lmdb_c.MDB_BAD_RSLOT: "Invalid reuse of reader locktable slot",
    lmdb_c.MDB_BAD_TXN: "Transaction must abort, has a child, or is invalid",
    lmdb_c.MDB_BAD_VALSIZE: "Unsupported size of key/DB name/data, or wrong DUPFIXED size",
    lmdb_c.MDB_BAD_DBI: "The specified DBI was changed unexpectedly",
}

other_error_code_lookup = {
    lmdb_c.EINVAL: ValueError("Invalid argument"),
    lmdb_c.ENOMEM: MemoryError("Out of memory"),
}


def check_return_code(rc: int):
    if rc == 0:
        return

    if rc in other_error_code_lookup:
        raise other_error_code_lookup[rc]

    raise LmdbException(rc, lmdb_error_code_lookup.get(rc, "Unknown"))
