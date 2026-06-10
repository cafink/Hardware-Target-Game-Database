# -*- coding: utf-8 -*-
"""
Reading SMDB (SourceMaterial DataBase) files.

An SMDB is a tab-separated text file with one file per line:

    SHA256 <tab> path <tab> SHA1 <tab> MD5 <tab> CRC32 <tab> size

Only the SHA256 and the path are guaranteed to be present; the remaining
columns are read when available. This single, lenient reader replaces the
two near-identical ``parse_database`` implementations that build_pack and
verify_pack used to carry.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional, Union

PathLike = Union[str, "os.PathLike[str]"]


@dataclass
class SmdbEntry:
    """One file recorded in an SMDB. Columns past the path are optional."""
    sha256: str
    path: str
    sha1: Optional[str] = None
    md5: Optional[str] = None
    crc32: Optional[str] = None
    size: Optional[int] = None


def read_entries(database_path: PathLike,
                 drop_initial_directory: bool = False) -> Iterator[SmdbEntry]:
    """
    Yield one :class:`SmdbEntry` per line of the SMDB at ``database_path``.

    With ``drop_initial_directory`` the leading path component is removed (so
    a pack folder can be named differently from the SMDB's top directory).
    Paths are normalised with :func:`os.path.normpath`.
    """
    with Path(database_path).open("r") as handle:
        for line in handle:
            fields = line.strip().split("\t")
            sha256 = fields[0]
            filename = fields[1]

            if drop_initial_directory:
                _, filename = filename.split("/", 1)
            # os.path.normpath (not pathlib) is kept on purpose: it collapses
            # "." / ".." and matches the relpath comparison verify_pack does.
            filename = os.path.normpath(filename)

            sha1 = fields[2] if len(fields) > 2 else None
            md5 = fields[3] if len(fields) > 3 else None
            crc32 = fields[4] if len(fields) > 4 else None
            size = int(fields[5]) if len(fields) > 5 else None

            yield SmdbEntry(sha256, filename, sha1, md5, crc32, size)
