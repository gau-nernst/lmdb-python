import os
from setuptools import Extension, setup
from Cython.Build import cythonize


lmdb_dir = "openldap/libraries/liblmdb"

extra_compile_args = []
if os.name == "nt":
    extra_compile_args.extend(["/link", "/DEFAULTLIB:Advapi32.lib"])

extensions = [
    Extension(
        "lmdb_python.lmdb_c",
        [
            "lmdb_python/lmdb_c.pyx",
            os.path.join(lmdb_dir, "mdb.c"),
            os.path.join(lmdb_dir, "midl.c"),
        ],
        include_dirs=[lmdb_dir],
        extra_compile_args=extra_compile_args,
    )
]

compiler_directives = {"language_level": 3, "embedsignature": True}

setup(
    name="lmdb-python",
    version="0.0.1",
    description="A Python binding for LMDB",
    author="Thien Tran",
    url="https://github.com/gau-nernst/lmdb-python",
    ext_modules=cythonize(extensions, compiler_directives=compiler_directives),
)
