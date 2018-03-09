#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import platform

from setuptools import setup
from distutils.command import install as distutils_install
from distutils.command.sdist import sdist as distutils_sdist

from replaceUsingPackageVersion.version import __version__


class install(distutils_install.install):
    """
    Custom install command
    """
    sub_commands = [
        ('install_lib', lambda self:False),
        ('install_headers', lambda self:False),
        ('install_scripts', lambda self:True),
        ('install_data', lambda self:True),
        ('install_egg_info', lambda self:False),
    ]


setup(
    name = "replace_using_package_version",
    version = __version__,
    author = "David Cassany",
    author_email = "dcassany@suse.com",
    description = "Replaces a regex  with the version value of a package",
    license = "GPL",
    keywords = "open build service",
    url = "https://github.com/davidcassany/obs-service-replace_using_package_version",
    packages=['replaceUsingPackageVersion'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX :: Linux',
        'Topic :: Development :: Tools :: Building',
    ],
    cmdclass = {
        'install':  install,
        'sdist':    distutils_sdist
    },
    scripts = ['replace_using_package_version'],
    data_files={'replace_using_package_version.service'}
)
