from . import lmdb_c


class LmdbException(Exception):
    def __init__(self, rc: int):
        self.rc = rc
        self.msg = lmdb_c.strerror(rc)
        super().__init__(f"{self.msg}. Return code {rc}")


def check_return_code(rc: int) -> None:
    if rc != 0:
        raise LmdbException(rc)
