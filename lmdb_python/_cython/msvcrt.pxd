cdef extern from "STDDEF.H":
    ctypedef extern long long intptr_t

cdef extern int _open_osfhandle(intptr_t osfhandle, int flags)
cdef extern intptr_t _get_osfhandle(int fd)
