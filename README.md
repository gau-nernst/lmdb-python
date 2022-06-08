# LMDB Python

[![Build and Test](https://github.com/gau-nernst/lmdb-python/actions/workflows/build.yaml/badge.svg)](https://github.com/gau-nernst/lmdb-python/actions/workflows/build.yaml)
[![Build wheels](https://github.com/gau-nernst/lmdb-python/actions/workflows/wheels.yaml/badge.svg)](https://github.com/gau-nernst/lmdb-python/actions/workflows/wheels.yaml)
![python >=3.7](https://img.shields.io/badge/python-%3E%3D3.7-informational)

Another Python bindings for LMDB.

This repo serves as a practice for me to learn how to use 3rd-party C/C++ libraries in Python using Cython. The compiled C extension is statically linked against the master branch of OpenLDAP [here](https://git.openldap.org/openldap/openldap).

## Installation

From wheels: To be provided

Pre-built wheels matrix

Python version | Linux (x86_64 and aarch64) | macOS (universal2) | Windows (x86_64 only)
--|--|--|--
3.7 | ✅ | ✅ (x86_64 only) | ✅ 
3.8 | ✅ | ✅ | ✅
3.9 | ✅ | ✅ | ✅
3.10 | ✅ | ✅ | ✅

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

On macOS, you might need to set some environment variables to use `clang` compiler

```bash
CC=clang CXX=clang++ pip install .
```

If you want to build against a specific version of LMDB, checkout the corresponding tag in the `openldap` submodule before installing the package

```bash
# assume you are inside 'lmdb-python' directory now
cd openldap
git checkout LMDB_0.9.29
cd ..
pip install .
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
