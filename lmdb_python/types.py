from typing import NamedTuple


class LmdbStat(NamedTuple):
    ms_psize: int
    ms_depth: int
    ms_branch_pages: int
    ms_leaf_pages: int
    ms_overflow_pages: int
    ms_entries: int


class LmdbEnvInfo(NamedTuple):
    me_mapsize: int
    me_last_pgno: int
    me_last_txnid: int
    me_maxreaders: int
    me_numreaders: int


class LmdbEnvFlags(NamedTuple):
    fixed_map: bool
    no_subdir: bool
    read_only: bool
    write_map: bool
    no_meta_sync: bool
    no_sync: bool
    map_async: bool
    no_tls: bool
    no_lock: bool
    no_readahead: bool
    no_meminit: bool


class LmdbDbFlags(NamedTuple):
    reverse_key: bool
    duplicate_sort: bool
    integer_key: bool
    duplicate_fixed: bool
    integer_duplicate: bool
    reverse_duplicate: bool
    create: bool
