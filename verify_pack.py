#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Use a database to verify files.
"""
import os
import sys
import argparse
from collections import defaultdict

import htgdb_common as common


__author__ = "Steve Matos (parts by aquaman)"
__date__ = "2020/11/28"
__version__ = "$Revision: 1.0"


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
        description="Use a database to verify files.")
    # Add support for the shared boolean flags.
    common.register_bool_type(parser)

    parser.add_argument("-f", "--folder",
                        dest="target_folder",
                        required=True,
                        help="set target folder")

    parser.add_argument("-d", "--database",
                        dest="target_database",
                        required=True,
                        help="set target database")

    parser.add_argument("-m", "--mismatch",
                        dest="mismatch_files",
                        default=None,
                        help="list mismatch files")

    # Valid uses of this flag include: -l, -l true, -l yes, --new_line=1
    common.add_new_line_argument(parser)

    # Valid uses of this flag include: -x, -x true, -x yes,
    # --drop_initial_directory=1
    common.add_drop_initial_directory_argument(parser)

    return parser.parse_args(argv)


def parse_database(target_database, drop_initial_directory):
    """
    Store hash values and filenames in a database.
    """
    db = defaultdict(list)  # missing key's default value is an empty list
    number_of_entries = 0
    with open(target_database, "r") as target_database:
        for line in target_database:
            hash_sha256, filename, other_hash = line.strip().split("\t", 2)
            number_of_entries += 1

            if drop_initial_directory:
                first_level, filename = filename.split("/", 1)

            filename = os.path.normpath(filename)
            db[hash_sha256].append(filename)

    return db, number_of_entries


def parse_folder(target_folder, db, end_line, new_line):
    """
    Read each file, produce a hash value and
     determine if it is in the correct location.
    """
    current_file = 0
    total_files = len([os.path.join(dp, f) for dp, dn, fn in
                       os.walk(os.path.expanduser(target_folder)) for f in fn])

    bad_location_files = []
    extra_files = []
    for dirpath, dirnames, filenames in os.walk(target_folder):
        if filenames:
            for f in filenames:
                filename = os.path.join(os.path.normpath(dirpath),
                                        os.path.normpath(f))
                absolute_filename = u'\\\\?\\' + os.path.abspath(filename)
                try:
                    hash_sha256 = common.sha256_file(filename)
                except FileNotFoundError:
                    hash_sha256 = common.sha256_file(absolute_filename)

                if hash_sha256 in db:
                    rel_path = os.path.relpath(filename, target_folder)

                    if rel_path in db[hash_sha256]:
                        # file found (correct location)
                        # remove file name from database
                        db[hash_sha256].remove(rel_path)
                    else:
                        # hash in database (file in bad location)
                        bad_location_files.append((filename, hash_sha256))
                else:
                    # hash not in database (extra file)
                    extra_files.append((filename, hash_sha256))

                current_file += 1
                common.print_message(
                    common.format_progress(current_file, total_files),
                    end_line)
    else:
        if not new_line:
            common.print_message(
                common.format_progress(current_file, total_files), "\n")

    return bad_location_files, extra_files


# *********************************************************************#
#                                                                      #
#                              Body                                    #
#                                                                      #
# *********************************************************************#

def write_mismatch_report(path, bad_location_files, extra_files,
                          missing_files):
    """
    Write the report of incorrect-location, extra and missing files.
    Each section is only written when it has entries.
    """
    bad_location_files.sort()
    extra_files.sort()
    missing_files.sort()

    with open(path, "w") as mismatch_files:
        if bad_location_files:
            print("Incorrect Location Files:", file=mismatch_files)
            for file, hash_sha256 in bad_location_files:
                print(os.path.abspath(file), hash_sha256,
                      sep="\t", file=mismatch_files)
            print("\n", file=mismatch_files)

        if extra_files:
            print("Extra Files:", file=mismatch_files)
            for file, hash_sha256 in extra_files:
                print(os.path.abspath(file), hash_sha256,
                      sep="\t", file=mismatch_files)
            print("\n", file=mismatch_files)

        if missing_files:
            print("Missing Files:", file=mismatch_files)
            for file, hash_sha256 in missing_files:
                print(file, hash_sha256, sep="\t", file=mismatch_files)
            print("\n", file=mismatch_files)


def main(argv=None):
    """Entry point: verify a folder against an SMDB and report mismatches."""
    args = parse_args(argv)
    end_line = "\n" if args.new_line else "\r"

    database, number_of_entries = parse_database(args.target_database,
                                                 args.drop_initial_directory)
    bad_location_files, extra_files = parse_folder(
        args.target_folder, database, end_line, args.new_line)

    missing_files = []
    for key in database:
        for file in database[key]:
            missing_files.append((file, key))

    # write information to log file only if there are any bad, extra
    # or missing files to report
    if args.mismatch_files and (bad_location_files or extra_files
                                or missing_files):
        write_mismatch_report(args.mismatch_files, bad_location_files,
                              extra_files, missing_files)

    print(f"incorrect location: {len(bad_location_files)}", file=sys.stdout)
    print(f"extra: {len(extra_files)}", file=sys.stdout)
    print(f"missing: {len(missing_files)}", file=sys.stdout)

    return 0


if __name__ == '__main__':
    sys.exit(main())
