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
    fixed_map: bool = False
    no_subdir: bool = False
    no_sync: bool = False
    read_only: bool = False
    no_meta_sync: bool = False
    write_map: bool = False
    map_async: bool = False
    no_tls: bool = False
    no_lock: bool = False
    no_readahead: bool = False
    no_meminit: bool = False


class LmdbDbFlags(NamedTuple):
    reverse_key: bool = False
    duplicate_sort: bool = False
    integer_key: bool = False
    duplicate_fixed: bool = False
    integer_duplicate: bool = False
    reverse_duplicate: bool = False
    create: bool = False
