# -*- coding: utf-8 -*-
"""
Shared helpers for the Hardware Target Game Database scripts.

This module collects logic that was previously copy-pasted across
parse_pack.py, build_pack.py, verify_pack.py and base_sorter.py:

* the custom argparse ``bool`` type and the common boolean flags,
* progress reporting on stdout,
* file hashing (a single SHA256 digest, or the full set used by the SMDB).

It deliberately contains no global state and runs nothing at import time, so
it is safe to import and unit-test in isolation.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import zlib
from typing import NamedTuple, Optional, TextIO

import sys

# Files are read in 128 KiB chunks so large ROMs are never held in memory.
CHUNK_SIZE = 128 * 1024


# --------------------------------------------------------------------------- #
#  Command-line helpers                                                        #
# --------------------------------------------------------------------------- #

def register_bool_type(parser: argparse.ArgumentParser) -> None:
    """
    Register the ``bool`` argparse type shared by every script.

    A value counts as true when it is one of "yes", "true", "t" or "1"
    (case-insensitive). This must be called before adding any argument that
    uses ``type="bool"``.
    """
    parser.register(
        "type", "bool",
        lambda value: value.lower() in ("yes", "true", "t", "1"),
    )


def add_new_line_argument(parser: argparse.ArgumentParser) -> None:
    """Add the ``-l/--new_line`` flag (UI subprocess monitoring)."""
    parser.add_argument(
        "-l", "--new_line",
        dest="new_line",
        default=False,
        nargs="?",
        const=True,
        type="bool",
        help=("Changes the way the stdout is printed, and allows for UI "
              "subprocess monitoring."),
    )


def add_drop_initial_directory_argument(parser: argparse.ArgumentParser) -> None:
    """Add the ``-x/--drop_initial_directory`` flag."""
    parser.add_argument(
        "-x", "--drop_initial_directory",
        dest="drop_initial_directory",
        default=False,
        nargs="?",
        const=True,
        type="bool",
        help=("Drops the 1st directory path in the SMDB file so you can "
              "customize the name."),
    )


def add_skip_existing_argument(parser: argparse.ArgumentParser) -> None:
    """Add the ``-s/--skip_existing`` flag."""
    parser.add_argument(
        "-s", "--skip_existing",
        dest="skip_existing",
        default=False,
        nargs="?",
        const=True,
        type="bool",
        help=("Skip files which already exist at the destination without "
              "overwriting them."),
    )


# --------------------------------------------------------------------------- #
#  Progress reporting                                                          #
# --------------------------------------------------------------------------- #

def print_message(text: str, end: str, file: TextIO = sys.stdout,
                  flush: bool = True) -> None:
    """Thin wrapper around ``print`` with the scripts' default arguments."""
    print(text, end=end, file=file, flush=flush)


def format_progress(current: int, total: Optional[int] = None) -> str:
    """
    Format a progress line.

    With ``total`` omitted the message matches parse_pack's single-counter
    form; with ``total`` given it matches the ``current / total`` form used by
    build_pack and verify_pack.
    """
    if total is None:
        return "processing file: {:>9}".format(current)
    return "processing file: {:>9} / {}".format(current, total)


# --------------------------------------------------------------------------- #
#  Hashing                                                                     #
# --------------------------------------------------------------------------- #

class FileDigests(NamedTuple):
    """The hash values and size recorded for one file in an SMDB."""
    sha256: str
    sha1: str
    md5: str
    crc32: str  # 8-digit zero-padded hex
    size: int


def sha256_file(path: str) -> str:
    """Return the hex SHA256 digest of the file at ``path``."""
    digest = hashlib.sha256()
    with open(path, "rb", buffering=0) as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_digests(path: str) -> FileDigests:
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
