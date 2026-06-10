# -*- coding: utf-8 -*-
"""argparse helpers shared by every command-line tool."""
from __future__ import annotations

import argparse


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


def add_drop_initial_directory_argument(
        parser: argparse.ArgumentParser) -> None:
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
