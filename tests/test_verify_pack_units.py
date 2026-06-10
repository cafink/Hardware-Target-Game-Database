# -*- coding: utf-8 -*-
"""In-process unit tests for verify_pack's importable helpers."""
import os

import verify_pack as vp


def write_db(path, lines):
    with open(str(path), "w") as handle:
        handle.write("\n".join(lines) + "\n")


def test_parse_database_maps_sha256_to_paths(tmp_path):
    db_path = tmp_path / "db.txt"
    write_db(db_path, [
        "\t".join(["a" * 64, "USA/a.bin", "rest"]),
        "\t".join(["b" * 64, "Japan/b.bin", "rest"]),
    ])

    db, count = vp.parse_database(str(db_path), False)

    assert count == 2
    assert db["a" * 64] == [os.path.normpath("USA/a.bin")]
    assert db["b" * 64] == [os.path.normpath("Japan/b.bin")]


def test_parse_database_drops_initial_directory(tmp_path):
    db_path = tmp_path / "db.txt"
    write_db(db_path, [
        "\t".join(["a" * 64, "topdir/USA/a.bin", "rest"]),
    ])

    db, _ = vp.parse_database(str(db_path), True)

    assert db["a" * 64] == [os.path.normpath("USA/a.bin")]


def test_write_mismatch_report_only_includes_nonempty_sections(tmp_path):
    report = tmp_path / "report.txt"

    vp.write_mismatch_report(
        str(report),
        bad_location_files=[],
        extra_files=[("/abs/extra.bin", "c" * 64)],
        missing_files=[],
    )

    text = report.read_text()
    assert "Extra Files:" in text
    assert "Incorrect Location Files:" not in text
    assert "Missing Files:" not in text
