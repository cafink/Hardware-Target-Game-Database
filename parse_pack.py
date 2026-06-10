#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
for a given folder, produce a list of file names with relative
paths and hash values.
"""
import os
import sys
import time
import argparse

import htgdb_common as common


__author__ = "aquaman"
__date__ = "2022/06/10"
__version__ = "$Revision: 4.6"


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
        description="list file names and produce hash values.")
    # Add support for the shared boolean flags.
    common.register_bool_type(parser)

    parser.add_argument("-f", "--folder",
                        dest="target_folder",
                        required=True,
                        help="set target folder")

    parser.add_argument("-o", "--output",
                        dest="output_file",
                        required=True,
                        help="set output file")

    # Valid uses of this flag include: -l, -l true, -l yes, --new_line=1
    common.add_new_line_argument(parser)

    return parser.parse_args(argv)


def parse_folder(target_folder, output_file, end_line, new_line):
    """
    read each file and produce a hash value.
    """
    # list folders and files to exclude
    banned_folders = ("/AUTO/", "/CPAK/",
                      "/Documentation/", "/ED64/",
                      "/EDFC/", "/EDGB/",
                      "/EDMD/", "/Extended SSF Dev Demo Sample - Krikzz/src/",
                      "/Firmware Backup/", "/GBASYS/",
                      "/Images/", "/MEGA/",
                      "/Manuals/", "/PALETTE/",
                      "/PATTERN/", "/SAVE/",
                      "/SNAP/", "/SOUNDS/",
                      "/SPED/", "/SYSTEM/",
                      "/System Test Images/",
                      "/System Volume Information/",
                      "/TBED/", "/TEXT/",
                      "/_PREVIEW/", "/menu/",
                      "/ntm_firmware_ver", "/sd2snes Themes/",
                      "/sd2snes/")
    banned_suffixes = (".001", ".002", ".003", ".004", ".005", ".006",
                       ".007", ".008", ".009", ".aps", ".asm",
                       ".bak", ".bat", ".bsa", ".bps",
                       ".bst", ".c", ".cht", ".dat", ".db", ".docx",
                       ".exe", ".ips", ".jpg", ".json", ".mso",
                       ".ods", ".odt", ".pc", ".pdf", ".srm",
                       ".sto", ".tmp", ".xdelta", ".xls",
                       "/os.pce", "/thumbs.db", "/menu.bin", "/desktop.ini",
                       "/.ds_store")  # must be lowercase

    with open(output_file, "w") as output_file:
        i = 0
        # make sure subfolders are alphanumerically sorted
        sorted_files = sorted(os.walk(target_folder), key=lambda x: x[0].lower())
        for dirpath, dirnames, filenames in sorted_files:
            if filenames:
                # make sure files are alphanumerically sorted
                filenames.sort(key=lambda v: (v.upper(), v[0].islower()))
                for f in filenames:
                    filename = os.path.join(os.path.normpath(dirpath), f)
                    absolute_filename = os.path.abspath(filename)
                    os.path.isfile(absolute_filename)
                    # convert to Unix format by default
                    filename = filename.replace("\\", "/")
                    # Report filenames with non-ASCII characters
                    try:
                        filename.encode('ascii')
                    except UnicodeEncodeError:
                        print("Error (non-ASCII character):", filename,
                              file=sys.stdout)
                        time.sleep(10)  # alternatively: sys.exit(1)
                    # exclude certain folders and files
                    if not (any(s in filename for s in banned_folders) or
                            filename.lower().endswith(banned_suffixes)):
                        try:
                            digests = common.file_digests(absolute_filename)
                        except FileNotFoundError:
                            # Windows default API is limited to paths of
                            # 260 characters
                            digests = common.file_digests(
                                u'\\\\?\\' + absolute_filename)

                        print(digests.sha256,
                              filename,
                              digests.sha1,
                              digests.md5,
                              digests.crc32,
                              digests.size,
                              sep="\t",
                              file=output_file)
                        i += 1
                        common.print_message(common.format_progress(i),
                                             end_line)
        else:
            if not new_line:
                common.print_message(common.format_progress(i), "\n")

    return None


def main(argv=None):
    """Entry point: parse arguments and produce the SMDB."""
    args = parse_args(argv)
    target_folder = args.target_folder
    output_file = args.output_file
    end_line = "\n" if args.new_line else "\r"
    if os.path.lexists(target_folder):
        target_folder = os.path.normpath(target_folder)
        parse_folder(target_folder, output_file, end_line, args.new_line)
    return 0


# *********************************************************************#
#                                                                      #
#                              Body                                    #
#                                                                      #
# *********************************************************************#

if __name__ == '__main__':
    sys.exit(main())
