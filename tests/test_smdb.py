# -*- coding: utf-8 -*-
"""Unit tests for the unified SMDB reader (htgdb.smdb)."""
import os

from htgdb import smdb


def write_db(path, lines):
    with open(str(path), "w") as handle:
        handle.write("\n".join(lines) + "\n")


def test_read_full_six_column_entry(tmp_path):
    db = tmp_path / "db.txt"
    write_db(db, ["\t".join(["a" * 64, "USA/a.bin", "s1", "m1",
                             "0000ffff", "42"])])

    entries = list(smdb.read_entries(str(db)))

    assert len(entries) == 1
    entry = entries[0]
    assert entry.sha256 == "a" * 64
    assert entry.path == os.path.normpath("USA/a.bin")
    assert entry.sha1 == "s1"
    assert entry.md5 == "m1"
    assert entry.crc32 == "0000ffff"
    assert entry.size == 42


def test_read_minimal_entry_has_optional_fields_none(tmp_path):
    # verify_pack only relies on the SHA256 + path being present.
    db = tmp_path / "db.txt"
    write_db(db, ["\t".join(["a" * 64, "USA/a.bin", "trailing"])])

    entry = list(smdb.read_entries(str(db)))[0]

    assert entry.sha256 == "a" * 64
    assert entry.path == os.path.normpath("USA/a.bin")
    assert entry.crc32 is None
    assert entry.size is None


def test_drop_initial_directory(tmp_path):
    db = tmp_path / "db.txt"
    write_db(db, ["\t".join(["a" * 64, "topdir/USA/a.bin", "s", "m",
                             "0000ffff", "1"])])

    entry = list(smdb.read_entries(str(db), drop_initial_directory=True))[0]

    assert entry.path == os.path.normpath("USA/a.bin")
