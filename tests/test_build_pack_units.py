# -*- coding: utf-8 -*-
"""In-process unit tests for build_pack's importable helpers."""
import os
import zipfile

import build_pack as bp


def write_db(path, lines):
    with open(str(path), "w") as handle:
        handle.write("\n".join(lines) + "\n")


def test_parse_database_indexes_by_sha256_and_crc(tmp_path):
    db_path = tmp_path / "db.txt"
    write_db(db_path, [
        "\t".join(["a" * 64, "USA/a.bin", "s", "m", "0000ffff", "10"]),
    ])

    db, count = bp.parse_database(str(db_path), False)

    assert count == 1
    normalized = os.path.normpath("USA/a.bin")
    assert db["a" * 64] == [normalized]
    assert db["0000ffff"] == [normalized]


def test_parse_database_drops_initial_directory(tmp_path):
    db_path = tmp_path / "db.txt"
    write_db(db_path, [
        "\t".join(["a" * 64, "topdir/USA/a.bin", "s", "m", "0000ffff", "10"]),
    ])

    db, _ = bp.parse_database(str(db_path), True)

    assert db["a" * 64] == [os.path.normpath("USA/a.bin")]


def test_collect_missing_files():
    # Simulated post-parse state: one missing file (both hashes survive) and
    # one found file (only its CRC entry remains after the SHA256 was deleted).
    db = {
        "a" * 64: ["USA/g.bin"],     # missing: sha256 survives
        "00ff00ff": ["USA/g.bin"],   # missing: crc survives (duplicate)
        "ffffffff": ["USA/f.bin"],   # found: lone crc entry, not a duplicate
    }

    missing, found = bp.collect_missing_files(db, number_of_entries=2)

    assert missing == [("g.bin", "a" * 64)]
    assert found == 1


def test_get_hashes_extracts_zip_entry_crc(tmp_path):
    zip_path = tmp_path / "games.zip"
    with zipfile.ZipFile(str(zip_path), "w") as zf:
        zf.writestr("rom.bin", "rom-contents")
    with zipfile.ZipFile(str(zip_path)) as zf:
        crc = "{0:08x}".format(zf.getinfo("rom.bin").CRC & 0xffffffff)

    hashes = bp.get_hashes(str(zip_path))

    # The zip's own sha256 entry has no archive metadata...
    assert any(info["archive"] is None for info in hashes.values())
    # ...and the entry CRC points back into the archive.
    assert crc in hashes
    assert hashes[crc]["archive"] == {"entry": "rom.bin", "type": "zip"}
