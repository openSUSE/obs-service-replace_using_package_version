#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import platform

from setuptools import setup
from distutils.command import install as distutils_install
from distutils.command.sdist import sdist as distutils_sdist

from replaceUsingPackageVersion.version import __version__

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


class install(distutils_install.install):
    """
    Custom install command
    """
    sub_commands = [
        ('install_lib', lambda self:True),
        ('install_headers', lambda self:False),
        ('install_scripts', lambda self:True),
        ('install_data', lambda self:False),
        ('install_egg_info', lambda self:True),
    ]


setup(
    name = "replace_using_package_version",
    version = __version__,
    author = "David Cassany",
    author_email = "dcassany@suse.com",
    description = ("An demonstration of how to create, document, and publish "
                                   "to the cheese shop a5 pypi.org."),
    license = "GPL",
    keywords = "open build service",
    url = "githubproject",
    packages=['replaceUsingPackageVersion'],
    long_description=read('README.md'),
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
    entry_points =  {
        'console_scripts': [(
            'replace_using_package_version='
            'replaceUsingPackageVersion.replace_using_package_version:main',
        )]
    }, 
)
