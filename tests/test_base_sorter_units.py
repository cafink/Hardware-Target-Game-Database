# -*- coding: utf-8 -*-
"""
In-process unit tests for base_sorter's pure helper functions.

These became importable in phase 2 (argparse no longer runs at import time),
so the region/type predicates and revision logic can be tested directly.
"""
import base_sorter as bs


def test_region_predicates():
    assert bs.is_USA("Sonic (USA).md") is True
    assert bs.is_USA("Sonic (Japan).md") is False
    assert bs.is_Japan("Zelda (Japan).md") is True
    assert bs.is_Europe("Tetris (Europe).md") is True
    assert bs.is_Europe("Tetris (USA).md") is False


def test_type_predicates():
    assert bs.is_beta("Game (Beta).md") is True
    assert bs.is_beta("Game (Beta 2).md") is True
    assert bs.is_beta("Game (USA).md") is False
    assert bs.is_demo("Game (Demo).md") is True
    assert bs.is_demo("Game (USA).md") is False


def test_other_regions_is_everything_else():
    assert bs.is_other_regions("Homebrew (World).md") is True
    assert bs.is_other_regions("Game (USA).md") is False
    assert bs.is_other_regions("Game (Japan).md") is False
    assert bs.is_other_regions("Game (Europe).md") is False


def test_is_revision_matches_same_base_name():
    assert bs.is_revision("Game (Rev 1).md", "Game (Rev 2).md") is True
    assert bs.is_revision("Game.md", "Game (Rev 1).md") is True
    assert bs.is_revision("Alpha.md", "Beta.md") is False


def test_get_earlier_revision_returns_lower():
    # A missing "(Rev n)" tag counts as revision 0.
    assert bs.get_earlier_revision(
        "Game (Rev 1).md", "Game (Rev 2).md") == "Game (Rev 1).md"
    assert bs.get_earlier_revision(
        "Game (Rev 2).md", "Game (Rev 1).md") == "Game (Rev 1).md"
    assert bs.get_earlier_revision(
        "Game.md", "Game (Rev 1).md") == "Game.md"
