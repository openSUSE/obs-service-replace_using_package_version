import pytest

from pytest_container import DerivedContainer

from replace_using_package_version.replace_using_package_version import (
    __doc__ as pkg_doc,
)

TESTFILE = "/opt/testfile"

CONTAINERFILE = rf"""RUN zypper -n in python3-pip find && zypper -n download apache2 python3
WORKDIR /opt/
COPY dist/*whl /opt/
RUN pip install /opt/*whl
RUN echo $'This is a testfile with some replacements like %%MINOR%%\n\
%NEVR%\n\
and a footer?' > {TESTFILE}
RUN mkdir -p /opt/repos/ && mv $(find /var/cache/zypp/ -name 'apache*') /opt/repos/
"""
TUMBLEWEED = DerivedContainer(
    base="registry.opensuse.org/opensuse/tumbleweed", containerfile=CONTAINERFILE
)
LEAP = DerivedContainer(
    base="registry.opensuse.org/opensuse/leap:15.3", containerfile=CONTAINERFILE
)
SLE = DerivedContainer(
    base="registry.suse.com/suse/sle15:15.3", containerfile=CONTAINERFILE
)


CONTAINER_IMAGES = [TUMBLEWEED, LEAP, SLE]


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
            fr"replace_using_package_version --file {fname} --outdir /opt/ --regex='footer' --package=apache2",
        ).stderr
    )


def test_failure_when_outdir_non_existent(auto_container):
    dirname = "/opt/non_existent"
    assert (
        f"Output directory {dirname} not found"
        in auto_container.connection.run_expect(
            [1],
            fr"replace_using_package_version --file {TESTFILE} --outdir {dirname} --regex='footer' --package=apache2",
        ).stderr
    )


def test_failure_when_invalid_parse_version(auto_container):
    assert (
        "Invalid value for this flag."
        in auto_container.connection.run_expect(
            [1],
            fr"replace_using_package_version --file {TESTFILE} --outdir /opt/ --regex='footer' --package='zypper' --parse-version='foobar'",
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
    assert auto_container_per_test.connection.file(
        TESTFILE
    ).content_string.strip().split("\n")[1] == ".".join(
        auto_container_per_test.connection.run_expect(
            [0], "rpm -q --qf '%{version}' /opt/repos/*rpm"
        )
        .stdout.strip()
        .split(".")[: index + 1]
    )
