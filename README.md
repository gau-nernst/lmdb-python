# LMDB Python

[![Build and Test](https://github.com/gau-nernst/lmdb-python/actions/workflows/build.yaml/badge.svg)](https://github.com/gau-nernst/lmdb-python/actions/workflows/build.yaml)
[![Build wheels](https://github.com/gau-nernst/lmdb-python/actions/workflows/wheels.yaml/badge.svg)](https://github.com/gau-nernst/lmdb-python/actions/workflows/wheels.yaml)
![python >=3.7](https://img.shields.io/badge/python-%3E%3D3.7-informational)

Another Python bindings for LMDB.

This repo serves as a practice for me to learn how to use 3rd-party C/C++ libraries in Python using Cython. The compiled C extension is statically linked against the master branch of OpenLDAP [here](https://git.openldap.org/openldap/openldap).

## Installation

From wheels:

```bash
pip install lmdb-python -f https://gau-nernst.github.io/lmdb-python/
```

The following pre-built wheels are provided (64-bit only)

Platform | Architecture
---------|---------
Linux | manylinux: x86_64 and aarch64; musllinux: x86_64 and aarch64
macOS | x86_64 (Intel) and arm64 (Apple Silicon)
Windows | AMD64, x86, and ARM64

Supported Python versions depend on [cibuildwheel](https://cibuildwheel.readthedocs.io/en/stable/options/#build-skip). macOS arm64 is Python 3.8+, Windows ARM64 is Python 3.9+, and the rest are Python 3.6+.

Due to GHA runners' limitations, the following wheels are not tested, thus not guaranteed to work:

- musllinux_aarch64
- macosx_arm64
- win_arm64

From source: Install directly from this GitHub repo

```bash
pip install git+https://github.com/gau-nernst/lmdb-python.git
```

Alternatively, you can clone the repo locally and install from the local clone (remember to clone recursively to get OpenLDAP LMDB C source)

```bash
git clone --recursive https://github.com/gau-nernst/lmdb-python.git
cd lmdb-python
pip install .
```

If you want to build against a specific version of LMDB, checkout the corresponding tag in the `openldap` submodule before installing the package

```bash
# assume you are inside 'lmdb-python' directory now
cd openldap
git checkout LMDB_0.9.30
```

## Usage

```python
from lmdb_python import Database

db = Database("test_db")
db.put(b"key", b"value")
assert db.get(b"key") == b"value"
```

## Run tests

Install `pytest` using either `pip` or `conda`, then run it.

```bash
pytest -v
```
