import pytest

from pytest_container import DerivedContainer
from pytest_container.container import ContainerData

from replace_using_package_version.replace_using_package_version import (
    __doc__ as pkg_doc,
)

TESTFILE = "/opt/testfile"
OBSINFO_VERSION = "1.6.3"

CONTAINERFILE = rf"""RUN zypper -n in python3-pip python3-rpm find && zypper -n download apache2 python3
WORKDIR /.build-srcdir/
COPY dist/*whl /opt/
RUN pip install /opt/*whl
RUN echo $'This is a testfile with some replacements like %%MINOR%%\n\
%NEVR%\n\
and a footer?' > {TESTFILE}

# remove the signkeys to mimic the state in OBS workers
RUN rpm -qa|grep '^gpg-pubkey'|xargs rpm -e
RUN mkdir -p /.build-srcdir/repos/ && mv $(find /var/cache/zypp/ -name 'apache*') /.build-srcdir/repos/

# copy our invalid version dummy rpm into the repos
COPY integration_tests/assets/hello-world-1.1.2.P3-1.x86_64.rpm /.build-srcdir/repos/

RUN mkdir /.build/ && echo $'RECIPEFILE="Dockerfile"\n\
BUILD_JOBS="12"\n\
BUILD_ARCH="x86_64:i686:i586:i486:i386"\n\
BUILD_RPMS=""\n\
BUILD_DIST="/.build/build.dist"' > /.build/build.data

RUN echo $'FROM registry.opensuse.org/opensuse/tumbleweed\n\
LABEL VERSION="%%VERSION%%"' > /.build-srcdir/Dockerfile

RUN echo $'name: somepackage\n\
version: {OBSINFO_VERSION}' > /.build-srcdir/somepackage.obsinfo

ENV BUILD_DIST="/.build/build.dist"
"""

TUMBLEWEED = DerivedContainer(
    base="registry.opensuse.org/opensuse/tumbleweed", containerfile=CONTAINERFILE
)
LEAP_15_3, LEAP_15_4 = (
    DerivedContainer(
        base=f"registry.opensuse.org/opensuse/leap:15.{ver}",
        containerfile=CONTAINERFILE,
    )
    for ver in (3, 4)
)
BCI_BASE_15_3, BCI_BASE_15_4 = (
    DerivedContainer(
        base=f"registry.suse.com/bci/bci-base:15.{ver}", containerfile=CONTAINERFILE
    )
    for ver in (3, 4)
)


CONTAINER_IMAGES = [TUMBLEWEED, LEAP_15_3, LEAP_15_4, BCI_BASE_15_3, BCI_BASE_15_4]


def test_help_works(auto_container):
    assert (
        pkg_doc.strip()
        in auto_container.connection.run_expect(
            [0], "replace_using_package_version -h"
        ).stdout.strip()
    )


def test_failure_when_file_non_existent(auto_container):
    fname = "/opt/non_existent"
    assert (
        f"File {fname} not found"
        in auto_container.connection.run_expect(
            [1],
            rf"replace_using_package_version --file {fname} --outdir /opt/ --regex='footer' --package=apache2",
        ).stderr
    )


def test_failure_when_outdir_non_existent(auto_container):
    dirname = "/opt/non_existent"
    assert (
        f"Output directory {dirname} not found"
        in auto_container.connection.run_expect(
            [1],
            rf"replace_using_package_version --file {TESTFILE} --outdir {dirname} --regex='footer' --package=apache2",
        ).stderr
    )


def test_failure_when_invalid_parse_version(auto_container):
    assert (
        "Invalid value for this flag."
        in auto_container.connection.run_expect(
            [1],
            rf"replace_using_package_version --file {TESTFILE} --outdir /opt/ --regex='footer' --package='zypper' --parse-version='foobar'",
        ).stderr
    )


def test_basic_replacement(auto_container_per_test):
    auto_container_per_test.connection.run_expect(
        [0],
        f"replace_using_package_version --file {TESTFILE} --outdir /opt/ --regex='footer' --parse-version='major' --replacement='header'",
    )
    assert (
        auto_container_per_test.connection.file(TESTFILE)
        .content_string.strip()
        .split("\n")[-1]
        == "and a header?"
    )


@pytest.mark.parametrize("version,index", [("major", 0), ("minor", 1), ("patch", 2)])
def test_version_replacement(auto_container_per_test, version: str, index: int):
    auto_container_per_test.connection.run_expect(
        [0],
        f"replace_using_package_version --file {TESTFILE} --outdir /opt/ --regex='%NEVR%' --package='zypper' --parse-version='{version}'",
    )
    assert auto_container_per_test.connection.file(
        TESTFILE
    ).content_string.strip().split("\n")[1] == ".".join(
        auto_container_per_test.connection.run_expect(
            [0], "rpm -q --qf '%{version}' zypper"
        )
        .stdout.strip()
        .split(".")[: index + 1]
    )


@pytest.mark.parametrize("version,index", [("major", 0), ("minor", 1), ("patch", 2)])
def test_version_replacement_from_local_file(
    auto_container_per_test, version: str, index: int
):
    auto_container_per_test.connection.run_expect(
        [0],
        f"replace_using_package_version --file {TESTFILE} --outdir /opt/ --regex='%NEVR%' --package='apache2' --parse-version='{version}'",
    )

    apache2_ver = auto_container_per_test.connection.run_expect(
        [0],
        "rpm -q --qf '%{version}' /.build-srcdir/repos/apache*rpm",
    ).stdout.strip()

    assert auto_container_per_test.connection.file(
        TESTFILE
    ).content_string.strip().split("\n")[1] == ".".join(
        apache2_ver.split(".")[: index + 1]
    )


@pytest.mark.parametrize("version,index", [("major", 0), ("minor", 1), ("patch", 2)])
def test_version_replacement_from_obsinfo_file(
    auto_container_per_test, version: str, index: int
):
    auto_container_per_test.connection.run_expect(
        [0],
        f"replace_using_package_version --file {TESTFILE} --outdir /opt/ --regex='%NEVR%' --package='somepackage' --parse-version='{version}'",
    )

    somepackage_ver = OBSINFO_VERSION

    assert auto_container_per_test.connection.file(
        TESTFILE
    ).content_string.strip().splitlines()[1] == ".".join(
        somepackage_ver.split(".")[: index + 1]
    )


def test_replacement_from_default_build_recipe(auto_container_per_test):
    auto_container_per_test.connection.run_expect(
        [0],
        f"replace_using_package_version --outdir /opt/ --regex='%%VERSION%%' --package='apache2'",
    )
    apache2_ver = auto_container_per_test.connection.run_expect(
        [0],
        "rpm -q --qf '%{version}' /.build-srcdir/repos/apache*rpm",
    ).stdout.strip()

    assert (
        auto_container_per_test.connection.file("/opt/Dockerfile").content_string
        == f"""FROM registry.opensuse.org/opensuse/tumbleweed\n\
LABEL VERSION="{apache2_ver}"
"""
    )


def test_version_replacement_from_invalid_python_version(
    auto_container_per_test: ContainerData,
) -> None:
    auto_container_per_test.connection.run_expect(
        [0],
        f"replace_using_package_version --file {TESTFILE} --outdir /opt/ --regex='%NEVR%' --package='hello-world'",
    )
    hello_world_ver = auto_container_per_test.connection.run_expect(
        [0],
        "rpm -q --qf '%{version}' /.build-srcdir/repos/hello-world*rpm",
    ).stdout.strip()

    assert (
        auto_container_per_test.connection.file(TESTFILE).content_string.splitlines()[1]
        == hello_world_ver
    )
