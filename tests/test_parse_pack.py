# -*- coding: utf-8 -*-
"""
Characterization tests for parse_pack.py.

parse_pack walks a folder and writes a tab-separated SMDB with one line per
file:  SHA256 <tab> path <tab> SHA1 <tab> MD5 <tab> CRC32 <tab> size
Paths are emitted in Unix (forward-slash) form, folders are walked in
case-insensitive order, and certain folders / suffixes are excluded.
"""


def read(path):
    with open(str(path), "r") as handle:
        return handle.read()


def test_basic_smdb_contents_and_order(tmp_path, run, make_tree, line):
    make_tree(tmp_path, {
        "pack": {
            "b.bin": "bbb",
            "a.bin": "aaa",
        },
    })
    out = tmp_path / "out.txt"

    result = run("parse_pack.py", ["-f", "pack", "-o", str(out)], cwd=tmp_path)

    assert result.returncode == 0
    # Files are alphabetised (A before B) within a folder.
    expected = (
        line("pack/a.bin", "aaa") + "\n" +
        line("pack/b.bin", "bbb") + "\n"
    )
    assert read(out) == expected


def test_subfolders_walked_case_insensitively(tmp_path, run, make_tree, line):
    make_tree(tmp_path, {
        "pack": {
            "Zelda": {"z.bin": "zzz"},
            "apple": {"a.bin": "aaa"},
        },
    })
    out = tmp_path / "out.txt"

    result = run("parse_pack.py", ["-f", "pack", "-o", str(out)], cwd=tmp_path)

    assert result.returncode == 0
    # "apple" sorts before "Zelda" when compared case-insensitively.
    expected = (
        line("pack/apple/a.bin", "aaa") + "\n" +
        line("pack/Zelda/z.bin", "zzz") + "\n"
    )
    assert read(out) == expected


def test_banned_folders_are_excluded(tmp_path, run, make_tree, line):
    make_tree(tmp_path, {
        "pack": {
            "keep.bin": "keep",
            "SYSTEM": {"skip.bin": "skip"},
            "menu": {"skip2.bin": "skip2"},
        },
    })
    out = tmp_path / "out.txt"

    result = run("parse_pack.py", ["-f", "pack", "-o", str(out)], cwd=tmp_path)

    assert result.returncode == 0
    # Only the top-level keep.bin survives; /SYSTEM/ and /menu/ are banned.
    assert read(out) == line("pack/keep.bin", "keep") + "\n"


def test_banned_suffixes_are_excluded(tmp_path, run, make_tree, line):
    make_tree(tmp_path, {
        "pack": {
            "game.bin": "game",
            "photo.jpg": "photo",
            "tool.exe": "tool",
            "notes.pdf": "notes",
        },
    })
    out = tmp_path / "out.txt"

    result = run("parse_pack.py", ["-f", "pack", "-o", str(out)], cwd=tmp_path)

    assert result.returncode == 0
    assert read(out) == line("pack/game.bin", "game") + "\n"


def test_missing_target_folder_writes_nothing(tmp_path, run):
    out = tmp_path / "out.txt"

    result = run("parse_pack.py",
                 ["-f", "does_not_exist", "-o", str(out)], cwd=tmp_path)

    # Script exits cleanly and never creates the output file.
    assert result.returncode == 0
    assert not out.exists()
