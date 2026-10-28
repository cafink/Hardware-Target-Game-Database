# -*- coding: utf-8 -*-
"""In-process unit tests for build_pack's importable helpers."""
import hashlib
import io
import os
import shutil
import zipfile

import rarfile

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


class FakeRarEntry:
    """Stands in for a rarfile.RarInfo."""

    def __init__(self, filename, crc=None, data=b"", is_dir=False):
        self.filename = filename
        self.CRC = crc
        self.data = data
        self._is_dir = is_dir

    def is_dir(self):
        return self._is_dir


class FakeRarFile:
    """
    Stands in for rarfile.RarFile, to construct entries the checked-in
    fixture doesn't contain: directories, CRC-less entries, and a missing
    extraction utility.
    """

    def __init__(self, entries, missing_tool=False):
        self.entries = entries
        self.missing_tool = missing_tool

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def infolist(self):
        return self.entries

    def open(self, entry):
        if self.missing_tool:
            raise rarfile.RarCannotExec("Cannot find working tool")
        return io.BytesIO(entry.data)


def read_rar_entries(monkeypatch, fake):
    monkeypatch.setattr(bp.rarfile, "RarFile", lambda filename: fake)
    return list(bp.RarArchive("unused.rar")._read_entries())


def test_rar_entry_without_crc_is_hashed_with_sha256(monkeypatch):
    fake = FakeRarFile([
        FakeRarEntry("dir", is_dir=True),
        FakeRarEntry("with-crc.bin", crc=0x3dc946f8),
        FakeRarEntry("no-crc.bin", data=b"rom-contents"),
    ])

    assert read_rar_entries(monkeypatch, fake) == [
        ("with-crc.bin", "3dc946f8"),
        ("no-crc.bin", hashlib.sha256(b"rom-contents").hexdigest()),
    ]


def test_rar_entry_without_crc_is_skipped_without_a_tool(monkeypatch, capsys):
    # Hashing a CRC-less entry means decompressing it, which needs the external
    # utility. Without one that entry is reported and skipped, but the rest of
    # the archive is still listed.
    fake = FakeRarFile([
        FakeRarEntry("no-crc.bin", data=b"rom-contents"),
        FakeRarEntry("with-crc.bin", crc=1),
    ], missing_tool=True)

    assert read_rar_entries(monkeypatch, fake) == [("with-crc.bin", "00000001")]
    assert "no rar utility found" in capsys.readouterr().out


def test_rar_entry_without_crc_is_matched_and_extracted(monkeypatch, tmp_path,
                                                        fixture):
    # Drive the fallback end to end with the real fixture, by hiding the CRCs
    # its entries do have: the entry must be decompressed and hashed, matched
    # against the SMDB by SHA256, then genuinely extracted.
    class CrcLessRarFile(rarfile.RarFile):
        def infolist(self):
            infos = super().infolist()
            for info in infos:
                info.CRC = None
            return infos

    monkeypatch.setattr(bp.rarfile, "RarFile", CrcLessRarFile)
    src = tmp_path / "src"
    src.mkdir()
    shutil.copyfile(fixture("rar-rom.rar"), str(src / "games.rar"))
    contents = b"rar-rom-contents" * 256
    db = {hashlib.sha256(contents).hexdigest(): [os.path.join("outpack",
                                                               "rom.bin")]}
    out = tmp_path / "out"

    bp.parse_folder(str(src), db, str(out), "copy", False, "\n", True)

    assert (out / "outpack" / "rom.bin").read_bytes() == contents
