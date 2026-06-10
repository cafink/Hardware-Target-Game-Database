# -*- coding: utf-8 -*-
"""
Unit tests for the shared helper module (htgdb_common).

Unlike the other test modules, these import the code directly and exercise it
in-process — the helpers are pure and carry no global state.
"""
import argparse
import hashlib
import zlib

import pytest

import htgdb_common as common


def make_parser():
    parser = argparse.ArgumentParser()
    common.register_bool_type(parser)
    return parser


@pytest.mark.parametrize("value,expected", [
    ("yes", True), ("true", True), ("t", True), ("1", True),
    ("YES", True), ("True", True),
    ("no", False), ("false", False), ("0", False), ("anything", False),
])
def test_bool_type_truthiness(value, expected):
    parser = make_parser()
    common.add_new_line_argument(parser)
    args = parser.parse_args(["--new_line", value])
    assert args.new_line is expected


def test_bool_flag_zero_argument_form_is_true():
    parser = make_parser()
    common.add_skip_existing_argument(parser)
    assert parser.parse_args(["-s"]).skip_existing is True


def test_bool_flag_defaults_to_false():
    parser = make_parser()
    common.add_drop_initial_directory_argument(parser)
    assert parser.parse_args([]).drop_initial_directory is False


def test_format_progress_without_total():
    assert common.format_progress(7) == "processing file:         7"


def test_format_progress_with_total():
    assert common.format_progress(7, 42) == "processing file:         7 / 42"


def test_sha256_file_matches_hashlib(tmp_path):
    payload = b"some rom bytes"
    target = tmp_path / "rom.bin"
    target.write_bytes(payload)
    assert common.sha256_file(str(target)) == hashlib.sha256(payload).hexdigest()


def test_file_digests_match_reference(tmp_path):
    payload = b"hello world" * 100
    target = tmp_path / "rom.bin"
    target.write_bytes(payload)

    digests = common.file_digests(str(target))

    assert digests.sha256 == hashlib.sha256(payload).hexdigest()
    assert digests.sha1 == hashlib.sha1(payload).hexdigest()
    assert digests.md5 == hashlib.md5(payload).hexdigest()
    assert digests.crc32 == "{0:08x}".format(zlib.crc32(payload) & 0xffffffff)
    assert digests.size == len(payload)


def test_file_digests_of_empty_file(tmp_path):
    target = tmp_path / "empty.bin"
    target.write_bytes(b"")
    digests = common.file_digests(str(target))
    assert digests.sha256 == (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
    assert digests.crc32 == "00000000"
    assert digests.size == 0
