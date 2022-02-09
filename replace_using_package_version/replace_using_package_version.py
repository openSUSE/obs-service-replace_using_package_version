#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018 SUSE Linux GmbH.  All rights reserved.
#
# This file is part of obs-service-replace_using_package_version.
#
#   obs-service-replace_using_package_version is free software: you can
#   redistribute it and/or modify it under the terms of the GNU General
#   Public License as published by the Free Software Foundation, either
#   version 3 of the License, or (at your option) any later version.
#
#   obs-service-replace_using_package_version is distributed in the hope
#   that it will be useful, but WITHOUT ANY WARRANTY; without even the
#   implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#   See the GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with obs-service-replace_using_package_version.  If not,
#   see <http://www.gnu.org/licenses/>.
#
"""
replace_with_package_version.py

Usage:
    replace_using_package_version.py -h
    replace_using_package_version.py --file=FILE --regex=REGEX --outdir=DIR
        (--package=PACKAGE | --replacement=REPLACEMENT)
        [--parse-version=DEPTH]
    replace_using_package_version.py --packages=PACKAGES --archive=ARCHIVE --outdir=DIR

Options:
    -h,--help                   : show this help message
    --outdir=DIR                : output directory
    --file=FILE                 : file to update
    --package=PACKAGE           : package to check
    --replacement=REPLACEMENT   : replacement string for any match
    --regex=REGEX               : regular expression for parsing file
    --parse-version=DEPTH       : parse the package version string to match
                                    major.minor.patch.patch_update format.
                                    It can be set to 'major', 'minor',
                                    'patch, patch_update and offset.
"""
from typing import Any, Dict
import docopt
import re
import os
import subprocess
import shutil
from pkg_resources import parse_version
from pathlib import Path

version_regex = {
    'major': r'^(\d+)',
    'minor': r'^(\d+(\.\d+){0,1})',
    'patch': r'^(\d+(\.\d+){0,2})',
    'patch_update': r'^(\d+(\.\d+){0,3})',
    'offset': r'^(?:\d+(?:\.\d+){0,3})[+-.~](?:git|svn|cvs)(\d+)'
}

# TODO: probably there is a better way to set the repositories path
RPM_DIR = './repos'


def extract_version(command_args: Dict[str, Any]) -> None:
    if not os.path.isfile(command_args['--file']):
        raise Exception('File {0} not found'.format(command_args['--file']))
    if not os.path.isdir(command_args['--outdir']):
        raise Exception(
            'Output directory {0} not found'.format(command_args['--outdir'])
        )

    filecopy = os.sep.join([
        command_args['--outdir'],
        os.path.basename(command_args['--file'])
    ])

    if command_args['--package']:
        parse_version = command_args['--parse-version']
        version = find_package_version(command_args['--package'], RPM_DIR)
        if parse_version and parse_version not in version_regex.keys():
            raise Exception((
                'Invalid value for this flag. Expected format is: '
                '--parse-version=[major|minor|patch|patch_update|offset]'
            ))
        elif parse_version:
            version = find_match_in_version(
                version_regex[parse_version], version
            )
        replacement = version
    else:
        replacement = command_args['--replacement']

    apply_regex_to_file(
        command_args['--file'],
        filecopy,
        command_args['--regex'],
        replacement
    )


def repack_rpms(command_args) -> None:
    packages = command_args["--packages"].split(",")
    archive = os.path.splitext(command_args["--archive"])

    for pkg in packages:
        for root, _, files in os.walk(RPM_DIR):
            packages = [
                f for f in files if f.endswith('rpm') and pkg in f
            ]
            for pkg in packages:
                rpm_file = os.path.realpath(os.path.join(root, pkg))
                rpm2cpio = subprocess.Popen(["rpm2cpio", rpm_file], stdout=subprocess.PIPE)
                Path("./archive_dir", ).mkdir(parents=True, exist_ok=True)
                res = subprocess.run(
                    ["cpio", "-idmv"],
                    stdin=rpm2cpio.stdout,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                    cwd="archive_dir"
                )
                rpm2cpio.wait()
                res.check_returncode()

    shutil.make_archive(archive[0], archive[1].replace(".", ""), root_dir="archive_dir")
    shutil.copy(command_args["--archive"], os.path.join(command_args["--outdir"], command_args["--archive"]))


def main():
    """
    main-entry point for program, expects dict with arguments from docopt()
    """
    command_args = docopt.docopt(__doc__)

    if command_args.get("--archive", None) is not None and command_args.get("--archive", None) is not None:
        repack_rpms(command_args)
    else:
        extract_version(command_args)


def apply_regex_to_file(input_file, output_file, regex, replacement):
    with open(input_file, 'r') as in_file:
        contents = in_file.read()

    with open(output_file, 'w') as out_file:
        out_file.write(re.sub(regex, replacement, contents))


def find_package_version(package, rpm_dir):
    try:
        version = get_pkg_version(package)
    except Exception:
        # If package is not found in rpmdb check local repositories
        version = parse_version('')
        for root, _, files in os.walk(rpm_dir):
            packages = [
                f for f in files if f.endswith('rpm') and package in f
            ]
            for pkg in packages:
                rpm_file = os.path.realpath(os.path.join(root, pkg))
                if get_pkg_name_from_rpm(rpm_file) == package:
                    rpm_version = get_pkg_version_from_rpm(rpm_file)
                    if rpm_version >= version:
                        version = rpm_version
    if not str(version):
        raise Exception('Package version not found')
    return str(version)


def find_match_in_version(regexpr, version):
    search = re.search(regexpr, version)
    if search is None:
        return version
    else:
        return search.group(1)


def run_command(command):
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ
    )
    output, error = process.communicate()
    if process.returncode != 0:
        if not error:
            error = bytes(b'(no output on stderr)')
        if not output:
            output = bytes(b'(no output on stdout)')
        raise Exception((
            'Command "{0}" failed\n\tstdout: {1}\n'
            '\tstderr: {2}'
        ).format(' '.join(command), output.decode(), error.decode()))
    return output.decode()


def get_pkg_name_from_rpm(rpm_file):
    command = [
        'rpm', '-qp', '--queryformat', '%{NAME}', rpm_file
    ]
    return run_command(command)


def get_pkg_version_from_rpm(rpm_file):
    command = [
        'rpm', '-qp', '--queryformat', '%{VERSION}', rpm_file
    ]
    return parse_version(run_command(command))


def get_pkg_version(package):
    command = [
        'rpm', '-q', '--queryformat', '%{VERSION}', package
    ]
    return parse_version(run_command(command))


def init(__name__):
    if __name__ == '__main__':
        main()


init(__name__)
