#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
replace_with_package_version.py

Usage:
    replace_using_package_version.py -h
    replace_using_package_version.py --file=FILE --regex=REGEX --outdir=DIR
        (--package=PACKAGE | --replacement=REPLACEMENT)

Options:
    -h,--help                   : show this help message
    --outdir=DIR                : output directory
    --file=FILE                 : file to update
    --package=PACKAGE           : package to check
    --replacement=REPLACEMENT   : replacement string for any match
    --regex=REGEX               : regular expression for parsing
"""
import docopt
import re
import os
import subprocess
from pkg_resources import parse_version


def main():
    """
    main-entry point for program, expects dict with arguments from docopt()
    """
    # TODO: probably there is a better way to set the repositories path
    rpm_dir = './repos'

    command_args = docopt.docopt(__doc__)

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
        version = find_package_version(command_args['--package'], rpm_dir)
        replacement = version
    else:
        replacement = command_args['--replacement']

    apply_regex_to_file(
        command_args['--file'],
        filecopy,
        command_args['--regex'],
        replacement
    )


def apply_regex_to_file(input_file, output_file, regex, replacement):
    with open(input_file, 'r') as in_file:
        contents = in_file.read()

    with open(output_file, 'w') as out_file:
        out_file.write(re.sub(regex, replacement, contents))


def find_package_version(package, rpm_dir):
    try:
        version = get_pkg_version(package)
    except Exception:
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
