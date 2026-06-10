# -*- coding: utf-8 -*-
"""
Characterization tests for base_sorter.py.

base_sorter reorganises an unsorted folder in place.  It detects region and
type from parenthesised tags in the file name, moves earlier revisions aside,
and finally groups each region's files into alphabetical batch folders.  These
tests pin down the exact directory layout it produces (quirks included, e.g.
the double-nested "<N> Japan - A-Z/Japan - A-Z/" folders for non-USA regions).
"""
import os


def relfiles(base):
    """Return the sorted list of file paths (relative to base, Unix slashes)."""
    base = str(base)
    found = []
    for dirpath, _dirnames, filenames in os.walk(base):
        for name in filenames:
            rel = os.path.relpath(os.path.join(dirpath, name), base)
            found.append(rel.replace(os.sep, "/"))
    return sorted(found)


def make_games(make_tree, tmp_path, names):
    files = {name: "data-" + name for name in names}
    make_tree(tmp_path, {"games": files})
    return tmp_path / "games"


def test_full_sort_layout(tmp_path, run, make_tree):
    games = make_games(make_tree, tmp_path, [
        "Sonic (USA).md",
        "Mario (USA).md",
        "Zelda (Japan).md",
        "Tetris (Europe).md",
        "Homebrew (World).md",
        "Beta Game (Beta).md",
        "Demo Game (Demo).md",
        "Rev Game (Rev 1).md",
        "Rev Game.md",
    ])

    result = run("base_sorter.py", ["-i", "."], cwd=games)

    assert result.returncode == 0
    assert relfiles(games) == sorted([
        # USA is grouped directly under the source folder.
        "1 USA - A-S/Mario (USA).md",
        "1 USA - A-S/Sonic (USA).md",
        # Non-USA regions get an extra nested batch folder.
        "2 Europe - A-Z/Europe - A-T/Tetris (Europe).md",
        "2 Japan - A-Z/Japan - A-Z/Zelda (Japan).md",
        "2 Other Regions - A-Z/Other Regions - A-R/Homebrew (World).md",
        # The higher revision keeps its region; the base name is the "earlier"
        # revision and is moved into Revisions.
        "2 Other Regions - A-Z/Other Regions - A-R/Rev Game (Rev 1).md",
        "4 Beta, Prototypes, Revisions/Betas/Beta Game (Beta).md",
        "4 Beta, Prototypes, Revisions/Revisions/Rev Game.md",
        "4 Beta, Prototypes, Revisions/Samples/Demo Game (Demo).md",
    ])


def test_discs_are_grouped_into_per_game_folders(tmp_path, run, make_tree):
    games = make_games(make_tree, tmp_path, [
        "FF7 (USA) (Disc 1).md",
        "FF7 (USA) (Disc 2).md",
        "Single (USA).md",
    ])

    result = run("base_sorter.py", ["-i", ".", "-d"], cwd=games)

    assert result.returncode == 0
    assert relfiles(games) == sorted([
        "1 USA - A-S/FF7 (USA)/FF7 (USA) (Disc 1).md",
        "1 USA - A-S/FF7 (USA)/FF7 (USA) (Disc 2).md",
        "1 USA - A-S/Single (USA)/Single (USA).md",
    ])


def test_file_type_filter_leaves_other_files_untouched(tmp_path, run,
                                                       make_tree):
    games = make_games(make_tree, tmp_path, [
        "Game (USA).md",
        "Game (USA).txt",
    ])

    result = run("base_sorter.py", ["-i", ".", "-t", "md"], cwd=games)

    assert result.returncode == 0
    files = relfiles(games)
    # Only the .md file is sorted; the .txt is left where it was.
    assert "1 USA - A-G/Game (USA).md" in files
    assert "Game (USA).txt" in files
