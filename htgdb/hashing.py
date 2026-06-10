# -*- coding: utf-8 -*-
"""File hashing helpers for the Hardware Target Game Database tools."""
from __future__ import annotations

import hashlib
import os
import zlib
from typing import NamedTuple, Union

# Files are read in 128 KiB chunks so large ROMs are never held in memory.
CHUNK_SIZE = 128 * 1024

# Anything that names a file on disk.
PathLike = Union[str, "os.PathLike[str]"]


class FileDigests(NamedTuple):
    """The hash values and size recorded for one file in an SMDB."""
    sha256: str
    sha1: str
    md5: str
    crc32: str  # 8-digit zero-padded hex
    size: int


def sha256_file(path: PathLike) -> str:
    """Return the hex SHA256 digest of the file at ``path``."""
    digest = hashlib.sha256()
    with open(path, "rb", buffering=0) as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_digests(path: PathLike) -> FileDigests:
    """
    Return every hash the SMDB records for ``path`` in a single read:
    SHA256, SHA1, MD5, CRC32 (8-hex) and the byte size.
    """
    sha256 = hashlib.sha256()
    sha1 = hashlib.sha1()
    md5 = hashlib.md5()
    crc = 0
    with open(path, "rb", buffering=0) as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            sha256.update(chunk)
            sha1.update(chunk)
            md5.update(chunk)
            crc = zlib.crc32(chunk, crc)
        size = os.path.getsize(handle.name)
    return FileDigests(
        sha256.hexdigest(),
        sha1.hexdigest(),
        md5.hexdigest(),
        "{0:08x}".format(crc & 0xffffffff),
        size,
    )
