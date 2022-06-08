import os
import re
from pathlib import Path

from Cython.Build import cythonize
from setuptools import Extension, setup

IS_WINDOWS = os.name == "nt"
CURRENT_DIR = Path("__file__").parent
LMDB_DIR = CURRENT_DIR / "openldap" / "libraries" / "liblmdb"
with open(Path(__file__).parent / "lmdb_python" / "version.py") as f:
    VERSION = re.search(r"([\d.]+)", f.readline().rstrip()).group(1)

ext = Extension(
    "lmdb_python._cython.lmdb_c",
    sources=[
        "lmdb_python/_cython/lmdb_c.pyx",
        str(LMDB_DIR / "mdb.c"),
        str(LMDB_DIR / "midl.c"),
    ],
    include_dirs=[str(LMDB_DIR)],
    extra_link_args=["/DEFAULTLIB:advapi32.lib"] if IS_WINDOWS else [],
)
compiler_directives = {"language_level": 3, "embedsignature": True}

setup(
    name="lmdb-python",
    version=VERSION,
    description="A Python binding for LMDB",
    author="Thien Tran",
    url="https://github.com/gau-nernst/lmdb-python",
    ext_modules=cythonize([ext], compiler_directives=compiler_directives),
    packages=["lmdb_python"],
)
