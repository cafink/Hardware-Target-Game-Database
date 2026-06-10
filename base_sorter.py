#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Game backup basic sorter.
"""
import argparse
import shutil
import os
import re
import sys
from pathlib import Path

from htgdb import cli

__author__ = "BuraBure"
__date__ = "2022/05/16"
__version__ = "$Revision: 1.0"


# *********************************************************************#
#                                                                      #
#                            CONSTANTS                                 #
#                                                                      #
# *********************************************************************#

REVISION_REGEX = r' \(Rev(\s\d)?\)'
REVISIONS_DIR = '4 Beta, Prototypes, Revisions/Revisions/'
BETAS_REGEX = r' \(Beta(\s\d)?\)'
BETAS_DIR = '4 Beta, Prototypes, Revisions/Betas/'
DEMOS_REGEX = r' \(Demo(\s\d)?\)'
DEMOS_DIR = '4 Beta, Prototypes, Revisions/Samples/'
USA_REGEX = r' \([^\)]*USA[^\)]*\)'
USA_TMP_DIR = '1 USA - TMP/'
JAPAN_REGEX = r' \([^\)]*Japan[^\)]*\)'
JAPAN_DIR = '2 Japan - A-Z/'
EUROPE_REGEX = r' \([^\)]*Europe[^\)]*\)'
EUROPE_DIR = '2 Europe - A-Z/'
OTHERS_DIR = '2 Other Regions - A-Z/'
DISC_REGEX = r'(^.*)\s\(Disc \d\)'
RESERVED_DIRS = [
    '^1 USA',
    '^2 Japan',
    '^2 Europe',
    '^2 Other Regions',
    '^2 Unlicensed',
    '^4 Beta, Prototypes, Revisions',
    '^4 Game Series Collection',
    '^4 Hacks',
    '^4 Homebrew',
    '^4 Translations',
    '^5 Tools & Service Test Carts',
]

blue = "\x1b[94;20m"
green = "\x1b[92;20m"
reset = "\x1b[0m"


# *********************************************************************#
#                                                                      #
#                            Functions                                 #
#                                                                      #
# *********************************************************************#

def parse_args(argv=None):
    """
    Parse arguments from command line.
    """
    parser = argparse.ArgumentParser(
        description="Game backup basic sorting.")

    # Add support for the shared boolean flags.
    cli.register_bool_type(parser)

    parser.add_argument("--debug",
                        dest="debug",
                        required=False,
                        nargs="?",
                        const=True,
                        type='bool',
                        help="debug output")

    parser.add_argument("-d", "--discs",
                        dest="discs",
                        required=False,
                        nargs="?",
                        const=True,
                        type='bool',
                        help="put discs into folders")

    parser.add_argument("-i", "--input_folder",
                        dest="source_dir",
                        required=True,
                        help="set source dir")

    parser.add_argument("-g", "--alphabetical_group_min_count",
                        dest="alphabetical_group_min_count",
                        required=False,
                        default=149,
                        help="the minimun file count for the alphabetical group dirs")

    parser.add_argument("-t", "--file_type",
                        dest="file_type",
                        required=False,
                        default=None,
                        help="only operate on a certain file type")

    return parser.parse_args(argv)


def debug_banner(msg, debug):
    if debug:
        print(green, '============================', reset)
        print(green, '+', msg.center(24, ' '), '+', reset)
        print(green, '============================', reset)


def get_file_list(directory, file_type):
    files = sorted((entry.name for entry in Path(directory).iterdir()),
                   key=str.lower)
    reserved_dir_regex = '|'.join(RESERVED_DIRS)
    safe_files = filter(lambda file: False if re.search(
        reserved_dir_regex, file) else True, files)

    if file_type is None:
        return safe_files
    else:
        return filter(lambda file: True if re.search(file_type + '$', file) else False, safe_files)


def move_files(file_list, destination, debug, process_discs=False):
    """
    Moves a list of files to a destination
    """
    if process_discs:
        move_disc_files(file_list, destination, debug)
        return

    __move_files(file_list, destination, debug)


def __move_files(file_or_file_list, destination, debug):
    for file in file_or_file_list if isinstance(file_or_file_list, list) else [file_or_file_list]:
        result_path = shutil.move(file, destination)
        if debug:
            print('Moved: "', reset, blue, file, reset, '" => "',
                  reset, blue, result_path, reset, '"', reset, sep='')


def move_disc_files(file_list, destination, debug):
    """
    Groups discs into folders and Moves them to a destination
    """
    for file in file_list:
        filename = os.path.basename(file)
        extensionless = Path(filename).stem
        discless_match = re.search(DISC_REGEX, filename)
        discless_name = discless_match.group(
            1) if discless_match != None else extensionless
        disc_dir = Path(destination) / discless_name
        disc_dir.mkdir(mode=511, parents=True, exist_ok=True)
        __move_files(file, disc_dir, debug)


def is_revision(prev_file, curr_file):
    return re.sub(REVISION_REGEX, '', prev_file) == re.sub(REVISION_REGEX, '', curr_file)


def get_earlier_revision(file_a, file_b):
    """
    Returns filepath that is the lower/earliest revision
    """
    rev_a_match = re.search(REVISION_REGEX, file_a)
    rev_b_match = re.search(REVISION_REGEX, file_b)

    rev_a = int(rev_a_match.group(1)) if rev_a_match != None else 0
    rev_b = int(rev_b_match.group(1)) if rev_b_match != None else 0

    if rev_a < rev_b:
        return file_a
    else:
        return file_b


def move_revisions(source_dir, options):
    """
    Moves all early revisions to the revisions dir
    """
    files = get_file_list(source_dir, options.file_type)
    prev_file = ''
    early_revisions = []
    # source_dir is already absolute, so this stays absolute too.
    revisions_dir = Path(source_dir) / REVISIONS_DIR

    for file in files:
        # file_abs stays a string: it is matched by the revision regexes.
        file_abs = os.path.join(source_dir, file)
        if is_revision(prev_file, file_abs):
            early_revisions.append(
                get_earlier_revision(prev_file, file_abs))
        prev_file = file_abs

    revisions_dir.mkdir(mode=511, parents=True, exist_ok=True)
    move_files(early_revisions, revisions_dir, options.debug, options.discs)


def is_beta(file):
    return True if re.search(BETAS_REGEX, file) != None else False


def is_demo(file):
    return True if re.search(DEMOS_REGEX, file) != None else False


def is_USA(file):
    return True if re.search(USA_REGEX, file) != None else False


def is_Japan(file):
    return True if re.search(JAPAN_REGEX, file) != None else False


def is_Europe(file):
    return True if re.search(EUROPE_REGEX, file) != None else False


def is_other_regions(file):
    return False if is_USA(file) | is_Japan(file) | is_Europe(file) else True


def move_files_conditionally(source_dir, destination_dir, predicate_fn,
                             options):
    """
    Moves files to destination if the predicate returns true
    """
    files = get_file_list(source_dir, options.file_type)
    abs_paths = []

    Path(destination_dir).mkdir(mode=511, parents=True, exist_ok=True)

    for file in files:
        # file_abs stays a string: it is matched by the region regexes.
        file_abs = os.path.join(source_dir, file)
        if predicate_fn(file_abs):
            abs_paths.append(file_abs)

    move_files(abs_paths, destination_dir, options.debug, options.discs)


def move_alphabetical_batch(batch, base_dir, dir_prefix, batch_starting_letter, batch_ending_letter, debug):
    batch_dir_name = dir_prefix + ' - ' + \
        batch_starting_letter + '-' + batch_ending_letter

    batch_dir_path = Path(base_dir) / batch_dir_name

    batch_dir_path.mkdir(mode=511, parents=True, exist_ok=True)
    move_files(batch, batch_dir_path, debug, False)


def group_files_alphabetically(base_dir, dir_prefix, options,
                               destination_dir=None):
    """
    Groups files into alphabetical dirs
    """
    files = get_file_list(base_dir, options.file_type)
    batch = []
    prev_file_name = '0'
    batch_starting_letter = 'A'
    destination_dir = base_dir if destination_dir is None else destination_dir

    for file in files:
        file_abs = os.path.join(base_dir, file)
        if (len(batch) >= int(options.alphabetical_group_min_count)) & (prev_file_name.lower()[0] != file.lower()[0]):
            move_alphabetical_batch(
                batch, destination_dir, dir_prefix, batch_starting_letter, prev_file_name.upper()[0], options.debug)
            batch = []
            batch_starting_letter = file.upper()[0]

        batch.append(file_abs)
        prev_file_name = file

    if len(batch) > 0:
        move_alphabetical_batch(
            batch, destination_dir, dir_prefix, batch_starting_letter, prev_file_name.upper()[0], options.debug)


# *********************************************************************#
#                                                                      #
#                              Body                                    #
#                                                                      #
# *********************************************************************#

def main(argv=None):
    """Entry point: sort a folder of game backups in place."""
    options = parse_args(argv)
    source_dir = Path(os.path.abspath(options.source_dir))

    debug_banner('MOVING REVISIONS', options.debug)
    move_revisions(source_dir, options)

    debug_banner('MOVING BETAS', options.debug)
    move_files_conditionally(source_dir, source_dir / BETAS_DIR,
                             is_beta, options)

    debug_banner('MOVING DEMOS', options.debug)
    move_files_conditionally(source_dir, source_dir / DEMOS_DIR,
                             is_demo, options)

    debug_banner('MOVING USA', options.debug)
    move_files_conditionally(source_dir, source_dir / USA_TMP_DIR,
                             is_USA, options)

    debug_banner('MOVING JAPAN', options.debug)
    move_files_conditionally(source_dir, source_dir / JAPAN_DIR,
                             is_Japan, options)

    debug_banner('MOVING EUROPE', options.debug)
    move_files_conditionally(source_dir, source_dir / EUROPE_DIR,
                             is_Europe, options)

    debug_banner('MOVING OTHER REGIONS', options.debug)
    move_files_conditionally(source_dir, source_dir / OTHERS_DIR,
                             is_other_regions, options)

    debug_banner('GROUPING USA', options.debug)
    usa_tmp_dir_abs = source_dir / USA_TMP_DIR
    group_files_alphabetically(usa_tmp_dir_abs, '1 USA', options, source_dir)
    usa_tmp_dir_abs.rmdir()

    debug_banner('GROUPING JAPAN', options.debug)
    group_files_alphabetically(source_dir / JAPAN_DIR, 'Japan', options)

    debug_banner('GROUPING EUROPE', options.debug)
    group_files_alphabetically(source_dir / EUROPE_DIR, 'Europe', options)

    debug_banner('GROUPING OTHER REGIONS', options.debug)
    group_files_alphabetically(source_dir / OTHERS_DIR, 'Other Regions',
                               options)

    return 0


if __name__ == '__main__':
    sys.exit(main())
