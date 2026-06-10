# -*- coding: utf-8 -*-
"""stdout progress reporting shared by the tools."""
from __future__ import annotations

import sys
from typing import Optional, TextIO


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
