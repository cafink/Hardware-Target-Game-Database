# -*- coding: utf-8 -*-
"""
Characterization tests for verify_pack.py.

verify_pack hashes every file in a folder and compares it against an SMDB,
reporting three categories on stdout:
    incorrect location: N   (right hash, wrong relative path)
    extra: N                (hash not present in the SMDB)
    missing: N              (SMDB entry with no matching file)
With -x the leading directory component of each SMDB path is dropped, which is
how a pack folder named differently from the SMDB's top directory is matched.
"""


def write_db(path, lines):
    with open(str(path), "w") as handle:
        handle.write("\n".join(lines) + "\n")


def counts(stdout):
    """Parse the three summary numbers from verify_pack's stdout."""
    result = {}
    for token in ("incorrect location", "extra", "missing"):
        for raw in stdout.splitlines():
            if raw.startswith(token + ":"):
                result[token] = int(raw.split(":")[1])
    return result


def test_all_files_present_and_correct(tmp_path, run, make_tree, line):
    make_tree(tmp_path, {
        "pack": {
            "USA": {"a.bin": "aaa"},
            "Japan": {"b.bin": "bbb"},
        },
    })
    db = tmp_path / "db.txt"
    write_db(db, [
        line("pack/USA/a.bin", "aaa"),
        line("pack/Japan/b.bin", "bbb"),
    ])

    result = run("verify_pack.py",
                 ["-f", "pack", "-d", str(db), "-x"], cwd=tmp_path)

    assert result.returncode == 0
    assert counts(result.stdout) == {
        "incorrect location": 0, "extra": 0, "missing": 0,
    }


def test_extra_file_is_reported(tmp_path, run, make_tree, line):
    make_tree(tmp_path, {
        "pack": {
            "USA": {"a.bin": "aaa", "surprise.bin": "surprise"},
        },
    })
    db = tmp_path / "db.txt"
    write_db(db, [line("pack/USA/a.bin", "aaa")])

    result = run("verify_pack.py",
                 ["-f", "pack", "-d", str(db), "-x"], cwd=tmp_path)

    assert counts(result.stdout) == {
        "incorrect location": 0, "extra": 1, "missing": 0,
    }


def test_missing_file_is_reported(tmp_path, run, make_tree, line):
    make_tree(tmp_path, {
        "pack": {"USA": {"a.bin": "aaa"}},
    })
    db = tmp_path / "db.txt"
    write_db(db, [
        line("pack/USA/a.bin", "aaa"),
        line("pack/USA/gone.bin", "gone"),
    ])

    result = run("verify_pack.py",
                 ["-f", "pack", "-d", str(db), "-x"], cwd=tmp_path)

    assert counts(result.stdout) == {
        "incorrect location": 0, "extra": 0, "missing": 1,
    }


def test_misplaced_file_is_reported(tmp_path, run, make_tree, line):
    # Same content as the SMDB expects, but in the wrong sub-folder.
    make_tree(tmp_path, {
        "pack": {"Japan": {"a.bin": "aaa"}},
    })
    db = tmp_path / "db.txt"
    write_db(db, [line("pack/USA/a.bin", "aaa")])

    result = run("verify_pack.py",
                 ["-f", "pack", "-d", str(db), "-x"], cwd=tmp_path)

    # A misplaced file counts as BOTH an incorrect location and as missing:
    # the expected USA/a.bin slot is never satisfied, so it stays "missing".
    assert counts(result.stdout) == {
        "incorrect location": 1, "extra": 0, "missing": 1,
    }


def test_mismatch_report_file_sections(tmp_path, run, make_tree, line):
    make_tree(tmp_path, {
        "pack": {
            "USA": {"a.bin": "aaa"},        # correct
            "Japan": {"b.bin": "bbb"},      # misplaced (db expects USA/b.bin)
            "extra.bin": "extra",           # extra
        },
    })
    db = tmp_path / "db.txt"
    write_db(db, [
        line("pack/USA/a.bin", "aaa"),
        line("pack/USA/b.bin", "bbb"),
        line("pack/USA/missing.bin", "missing"),
    ])
    report = tmp_path / "mismatch.txt"

    result = run("verify_pack.py",
                 ["-f", "pack", "-d", str(db), "-x", "-m", str(report)],
                 cwd=tmp_path)

    assert result.returncode == 0
    # missing == 2: the explicitly-absent missing.bin, plus USA/b.bin whose
    # slot is left empty because b.bin turned up in the wrong folder.
    assert counts(result.stdout) == {
        "incorrect location": 1, "extra": 1, "missing": 2,
    }
    text = report.read_text()
    assert "Incorrect Location Files:" in text
    assert "Extra Files:" in text
    assert "Missing Files:" in text
    # The missing entry is listed by its SMDB-relative path.
    assert "missing.bin" in text


def test_without_drop_initial_directory(tmp_path, run, make_tree, line):
    # When the SMDB paths are already relative to the verified folder, no -x
    # is needed; this exercises the "do not drop first level" branch.
    make_tree(tmp_path, {"pack": {"USA": {"a.bin": "aaa"}}})
    db = tmp_path / "db.txt"
    write_db(db, [line("USA/a.bin", "aaa")])

    result = run("verify_pack.py",
                 ["-f", "pack", "-d", str(db)], cwd=tmp_path)

    assert result.returncode == 0
    assert counts(result.stdout) == {
        "incorrect location": 0, "extra": 0, "missing": 0,
    }


def test_new_line_flag_still_verifies(tmp_path, run, make_tree, line):
    # -l only changes the progress printing branch; the verdict is unchanged.
    make_tree(tmp_path, {"pack": {"USA": {"a.bin": "aaa"}}})
    db = tmp_path / "db.txt"
    write_db(db, [line("pack/USA/a.bin", "aaa")])

    result = run("verify_pack.py",
                 ["-f", "pack", "-d", str(db), "-x", "-l"], cwd=tmp_path)

    assert result.returncode == 0
    assert counts(result.stdout) == {
        "incorrect location": 0, "extra": 0, "missing": 0,
    }


def test_report_with_only_extra_files(tmp_path, run, make_tree, line):
    # Report written with just the "Extra Files" section present.
    make_tree(tmp_path, {
        "pack": {"USA": {"a.bin": "aaa", "extra.bin": "extra"}},
    })
    db = tmp_path / "db.txt"
    write_db(db, [line("pack/USA/a.bin", "aaa")])
    report = tmp_path / "mismatch.txt"

    result = run("verify_pack.py",
                 ["-f", "pack", "-d", str(db), "-x", "-m", str(report)],
                 cwd=tmp_path)

    assert result.returncode == 0
    text = report.read_text()
    assert "Extra Files:" in text
    assert "Incorrect Location Files:" not in text
    assert "Missing Files:" not in text


def test_report_with_only_missing_files(tmp_path, run, make_tree, line):
    # Report written with just the "Missing Files" section present.
    make_tree(tmp_path, {"pack": {"USA": {"a.bin": "aaa"}}})
    db = tmp_path / "db.txt"
    write_db(db, [
        line("pack/USA/a.bin", "aaa"),
        line("pack/USA/gone.bin", "gone"),
    ])
    report = tmp_path / "mismatch.txt"

    result = run("verify_pack.py",
                 ["-f", "pack", "-d", str(db), "-x", "-m", str(report)],
                 cwd=tmp_path)

    assert result.returncode == 0
    text = report.read_text()
    assert "Missing Files:" in text
    assert "Incorrect Location Files:" not in text
    assert "Extra Files:" not in text


def test_no_report_written_when_everything_matches(tmp_path, run, make_tree,
                                                   line):
    make_tree(tmp_path, {"pack": {"USA": {"a.bin": "aaa"}}})
    db = tmp_path / "db.txt"
    write_db(db, [line("pack/USA/a.bin", "aaa")])
    report = tmp_path / "mismatch.txt"

    run("verify_pack.py",
        ["-f", "pack", "-d", str(db), "-x", "-m", str(report)], cwd=tmp_path)

    # The report is only created when there is something to report.
    assert not report.exists()
