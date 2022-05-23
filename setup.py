import os
from setuptools import Extension, setup
from Cython.Build import cythonize


LMDB_DIR = "openldap/libraries/liblmdb"

extra_link_args = []
if os.name == "nt":
    extra_link_args.append("/DEFAULTLIB:advapi32.lib")

ext = Extension(
    "lmdb_python._cython.lmdb_c",
    [
        "lmdb_python/_cython/lmdb_c.pyx",
        os.path.join(LMDB_DIR, "mdb.c"),
        os.path.join(LMDB_DIR, "midl.c"),
    ],
    include_dirs=[LMDB_DIR],
    extra_link_args=extra_link_args,
)
extensions = [ext]

compiler_directives = {"language_level": 3, "embedsignature": True}

setup(
    name="lmdb-python",
    version="0.0.1",
    description="A Python binding for LMDB",
    author="Thien Tran",
    url="https://github.com/gau-nernst/lmdb-python",
    ext_modules=cythonize(extensions, compiler_directives=compiler_directives),
    packages=["lmdb_python"],
)
