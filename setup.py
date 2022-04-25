import os
from setuptools import Extension, setup
from Cython.Build import cythonize


lmdb_dir = "openldap/libraries/liblmdb"

extensions = [
    Extension(
        "lmdb_python.lmdb_python",
        [
            "lmdb_python/lmdb_python.pyx",
            os.path.join(lmdb_dir, "mdb.c"),
            os.path.join(lmdb_dir, "midl.c")
        ],
        include_dirs=[lmdb_dir],
    )
]

compiler_directives={
    'language_level': 3,
    'embedsignature': True
}

setup(
    ext_modules=cythonize(extensions, compiler_directives=compiler_directives)
)
