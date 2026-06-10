# -*- coding: utf-8 -*-
"""
Characterization tests for build_pack.py.

build_pack reads an SMDB, hashes every file under a source folder, and
reproduces the SMDB's directory layout in an output folder by copying /
hardlinking matching files (or extracting them out of zip archives).  It
reports coverage on stdout and can write a list of missing files.

Note: parse_database here splits each SMDB line into 5 columns
(sha256, path, sha1, md5, crc) and indexes files by BOTH their sha256 and
their crc, so the fixtures use full 6-column SMDB lines.
"""
import os
import zipfile


def write_db(path, lines):
    with open(str(path), "w") as handle:
        handle.write("\n".join(lines) + "\n")


def read(path):
    with open(str(path), "rb") as handle:
        return handle.read()


def test_copy_strategy_reproduces_layout(tmp_path, run, make_tree, line):
    make_tree(tmp_path, {"src": {"a.bin": "aaa", "b.bin": "bbb"}})
    db = tmp_path / "db.txt"
    write_db(db, [
        line("outpack/USA/a.bin", "aaa"),
        line("outpack/Japan/b.bin", "bbb"),
    ])
    out = tmp_path / "out"

    result = run("build_pack.py",
                 ["-i", "src", "-d", str(db), "-o", str(out),
                  "--file_strategy", "copy"],
                 cwd=tmp_path)

    assert result.returncode == 0
    assert read(out / "outpack" / "USA" / "a.bin") == b"aaa"
    assert read(out / "outpack" / "Japan" / "b.bin") == b"bbb"
    assert "coverage: 2/2 (100.0%)" in result.stdout


def test_hardlink_strategy_shares_inode(tmp_path, run, make_tree, line):
    make_tree(tmp_path, {"src": {"a.bin": "aaa"}})
    db = tmp_path / "db.txt"
    write_db(db, [line("outpack/USA/a.bin", "aaa")])
    out = tmp_path / "out"

    result = run("build_pack.py",
                 ["-i", "src", "-d", str(db), "-o", str(out),
                  "--file_strategy", "hardlink"],
                 cwd=tmp_path)

    assert result.returncode == 0
    src_file = tmp_path / "src" / "a.bin"
    dst_file = out / "outpack" / "USA" / "a.bin"
    assert os.path.samefile(str(src_file), str(dst_file))


def test_missing_file_reported_and_coverage(tmp_path, run, make_tree, line):
    make_tree(tmp_path, {"src": {"a.bin": "aaa"}})
    db = tmp_path / "db.txt"
    write_db(db, [
        line("outpack/USA/a.bin", "aaa"),
        line("outpack/USA/gone.bin", "gone"),
    ])
    out = tmp_path / "out"
    missing = tmp_path / "missing.txt"

    result = run("build_pack.py",
                 ["-i", "src", "-d", str(db), "-o", str(out),
                  "-m", str(missing)],
                 cwd=tmp_path)

    assert result.returncode == 0
    assert read(out / "outpack" / "USA" / "a.bin") == b"aaa"
    assert not (out / "outpack" / "USA" / "gone.bin").exists()
    assert "coverage: 1/2 (50.0%)" in result.stdout
    assert "gone.bin" in missing.read_text()


def test_extract_from_zip_archive(tmp_path, run, make_tree):
    # Build a zip whose entry's CRC we look up to drive the SMDB.
    src = tmp_path / "src"
    src.mkdir()
    zip_path = src / "games.zip"
    with zipfile.ZipFile(str(zip_path), "w") as zf:
        zf.writestr("rom.bin", "rom-contents")
    with zipfile.ZipFile(str(zip_path)) as zf:
        crc = "{0:08x}".format(zf.getinfo("rom.bin").CRC & 0xffffffff)

    # crc lands in the 5th column; build_pack indexes by it and extracts.
    db = tmp_path / "db.txt"
    dummy_sha = "0" * 64
    dummy_other = "0" * 40
    dummy_md5 = "0" * 32
    write_db(db, ["\t".join([dummy_sha, "outpack/USA/rom.bin",
                             dummy_other, dummy_md5, crc, "12"])])
    out = tmp_path / "out"

    result = run("build_pack.py",
                 ["-i", "src", "-d", str(db), "-o", str(out)],
                 cwd=tmp_path)

    assert result.returncode == 0
    assert read(out / "outpack" / "USA" / "rom.bin") == b"rom-contents"


def test_skip_existing_leaves_file_untouched(tmp_path, run, make_tree, line):
    make_tree(tmp_path, {
        "src": {"a.bin": "aaa"},
        "out": {"outpack": {"USA": {"a.bin": "preexisting"}}},
    })
    db = tmp_path / "db.txt"
    write_db(db, [line("outpack/USA/a.bin", "aaa")])
    out = tmp_path / "out"

    result = run("build_pack.py",
                 ["-i", "src", "-d", str(db), "-o", str(out),
                  "-s"],
                 cwd=tmp_path)

    assert result.returncode == 0
    # With --skip_existing the pre-existing file is not overwritten.
    assert read(out / "outpack" / "USA" / "a.bin") == b"preexisting"
