cdef extern from "STDDEF.H":
    ctypedef extern void* intptr_t

    int _open_osfhandle(intptr_t osfhandle, int flags)
    intptr_t _get_osfhandle(int fd)
