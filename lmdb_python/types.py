from collections import namedtuple


LmdbStat = namedtuple(
    "LmdbStat",
    [
        "ms_psize",
        "ms_depth",
        "ms_branch_pages",
        "ms_leaf_pages",
        "ms_overflow_pages",
        "ms_entries",
    ],
)
LmdbEnvInfo = namedtuple(
    "LmdbEnvInfo",
    [
        "me_mapsize",
        "me_last_pgno",
        "me_last_txnid",
        "me_maxreaders",
        "me_numreaders",
    ],
)
LmdbEnvFlags = namedtuple(
    "LmdbEnvFlags",
    [
        "fixed_map",
        "no_subdir",
        "read_only",
        "write_map",
        "no_meta_sync",
        "no_sync",
        "map_async",
        "no_tls",
        "no_lock",
        "no_readahead",
        "no_meminit",
    ],
)
LmdbDbFlags = namedtuple(
    "LmdbDbFlags",
    [
        "reverse_key",
        "duplicate_sort",
        "integer_key",
        "duplicate_fixed",
        "integer_duplicate",
        "reverse_duplicate",
        "creat",
    ],
)
