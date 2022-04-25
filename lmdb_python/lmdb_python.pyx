from typing import Iterable, Tuple

cimport lmdb_python.lmdb as lmdb


error_code_lookup = {
    lmdb.EINVAL: 'Invalid argument',
    lmdb.ENOMEM: 'Out of memory',
    lmdb.MDB_KEYEXIST: 'key/data pair already exists',
    lmdb.MDB_NOTFOUND: 'key/data pair not found (EOF)',
    lmdb.MDB_PAGE_NOTFOUND: 'Requested page not found - this usually indicates corruption',
    lmdb.MDB_CORRUPTED: 'Located page was wrong type',
    lmdb.MDB_PANIC: 'Update of meta page failed or environment had fatal error',
    lmdb.MDB_VERSION_MISMATCH: 'Environment version mismatch',
    lmdb.MDB_INVALID: 'File is not a valid LMDB file',
    lmdb.MDB_MAP_FULL: 'Environment mapsize reached',
    lmdb.MDB_DBS_FULL: 'Environment maxdbs reached',
    lmdb.MDB_READERS_FULL: 'Environment maxreaders reached',
    lmdb.MDB_TLS_FULL: 'Too many TLS keys in use - Windows only',
    lmdb.MDB_TXN_FULL: 'Txn has too many dirty pages',
    lmdb.MDB_CURSOR_FULL: 'Cursor stack too deep - internal error',
    lmdb.MDB_PAGE_FULL: 'Page has not enough space - internal error',
    lmdb.MDB_MAP_RESIZED: 'Database contents grew beyond environment mapsize',
    lmdb.MDB_INCOMPATIBLE: 'Operation and DB incompatible, or DB type changed',
    lmdb.MDB_BAD_RSLOT: 'Invalid reuse of reader locktable slot',
    lmdb.MDB_BAD_TXN: 'Transaction must abort, has a child, or is invalid',
    lmdb.MDB_BAD_VALSIZE: 'Unsupported size of key/DB name/data, or wrong DUPFIXED size',
    lmdb.MDB_BAD_DBI: 'The specified DBI was changed unexpectedly'
}


cdef check_return_code(int rc):
    if rc != 0:
        raise RuntimeError(f"{error_code_lookup.get(rc, 'Unknown')}. Return code {rc}")


def get_lmdb_version() -> str:
    return f'{lmdb.MDB_VERSION_MAJOR}.{lmdb.MDB_VERSION_MINOR}.{lmdb.MDB_VERSION_PATCH}'


cdef class LmdbDatabase:
    cdef lmdb.MDB_env* env
    cdef lmdb.MDB_txn* txn    
    cdef lmdb.MDB_dbi dbi

    def __cinit__(self, db_name: str, no_subdir: bool = False, read_only: bool = False):
        self._create_env()
        env_flags = 0
        if no_subdir:
            env_flags |= lmdb.MDB_NOSUBDIR
        if read_only:
            env_flags |= lmdb.MDB_RDONLY
        self._open_env(db_name.encode('utf-8'), env_flags, 0664)
        self._begin_txn(0)
        self._open_dbi()
        self._commit_txn()
        
    cdef _create_env(self):
        rc = lmdb.mdb_env_create(&self.env)
        check_return_code(rc)
    
    cdef _open_env(self, char* db_name, int flags, mode):
        rc = lmdb.mdb_env_open(self.env, db_name, flags, mode)
        check_return_code(rc)

    cdef _open_dbi(self):
        rc = lmdb.mdb_dbi_open(self.txn, NULL, 0, &self.dbi)
        check_return_code(rc)

    cdef _close_dbi(self):
        lmdb.mdb_dbi_close(self.env, self.dbi)

    cdef _begin_txn(self, int flag):
        rc = lmdb.mdb_txn_begin(self.env, NULL, flag, &self.txn)
        check_return_code(rc)

    cdef _commit_txn(self):
        rc = lmdb.mdb_txn_commit(self.txn)
        check_return_code(rc)

    cdef _abort_txn(self):
        lmdb.mdb_txn_abort(self.txn)

    cdef _put(self, lmdb.MDB_val* key, lmdb.MDB_val* value):
        rc = lmdb.mdb_put(self.txn, self.dbi, key, value, 0)
        check_return_code(rc)

    cdef _get(self, lmdb.MDB_val* key, lmdb.MDB_val* value):
        rc = lmdb.mdb_get(self.txn, self.dbi, key, value)
        check_return_code(rc)

    cdef _del(self, lmdb.MDB_val* key):
        rc = lmdb.mdb_del(self.txn, self.dbi, key, NULL)
        check_return_code(rc)

    def put(self, key: bytes, value: bytes):
        self._begin_txn(0)
        cdef lmdb.MDB_val _key
        cdef lmdb.MDB_val _value

        _key.mv_size = len(key)
        _key.mv_data = <char*> key

        _value.mv_size = len(value)
        _value.mv_data = <char*> value

        self._put(&_key, &_value)
        self._commit_txn()
        
    def get(self, key: bytes) -> bytes:
        self._begin_txn(lmdb.MDB_RDONLY)
        cdef lmdb.MDB_val _key
        cdef lmdb.MDB_val _value

        key_c = key
        _key.mv_size = len(key)
        _key.mv_data = <char*> key

        self._get(&_key, &_value)
        value = (<char*> _value.mv_data)[:_value.mv_size]
        self._abort_txn()
        return value

    def delete(self, key: bytes):
        self._begin_txn(0)
        cdef lmdb.MDB_val _key

        _key.mv_size = len(key)
        _key.mv_data = <char*> key

        self._del(&_key)
        self._commit_txn()

    def put_batch(self, items: Iterable[Tuple[bytes, bytes]]):
        self._begin_txn(0)
        cdef lmdb.MDB_val _key
        cdef lmdb.MDB_val _value

        for key, value in items:
            _key.mv_size = len(key)
            _key.mv_data = <char*> key

            _value.mv_size = len(value)
            _value.mv_data = <char*> value

            self._put(&_key, &_value)

        self._commit_txn()

    def get_batch(self, keys: Iterable[bytes]) -> Tuple[bytes]:
        self._begin_txn(lmdb.MDB_RDONLY)
        cdef lmdb.MDB_val _key
        cdef lmdb.MDB_val _value

        values = []
        for key in keys:
            _key.mv_size = len(key)
            _key.mv_data = <char*> key
            
            self._get(&_key, &_value)
            data = (<char*> _value.mv_data)[:_value.mv_size]
            values.append(data)

        self._abort_txn()
        return tuple(values)

    def __dealloc__(self):
        self._close_dbi()
        if self.env is not NULL:
            lmdb.mdb_env_close(self.env)
