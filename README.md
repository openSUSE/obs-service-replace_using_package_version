# obs-service-replace_using_package_version

[![CI](https://github.com/openSUSE/obs-service-replace_using_package_version/actions/workflows/ci.yml/badge.svg)](https://github.com/openSUSE/obs-service-replace_using_package_version/actions/workflows/ci.yml)

An OBS service to replace a regex with some package version available
in the build time environment or repositories.

This service makes sense mostly in `buildtime` mode.

## Development

This is a python project that makes use of setuptools and virtual environment.

To set the development environment consider the following commands:

```bash
# Get into the repository folder
$ cd obs-service-replace_using_package_version

# Initiate the python3 virtualenv
$ poetry shell

# Install the project and dependencies into the virtual env
$ poetry install

# Run tests and code style checks
$ tox
```

In case the development host is on a distro which does not include poetry
one can still manually create a virtual environment and install poetry there.

```bash
# Create a virtual env
$ python3 -v env .env3

# Load the venv
$ source .env3/bin/activate

# Install poetry
$ pip install poetry

# Install the project and dependencies to the virtual env
$ poetry install
```

## Usage

Consider a `_service` file that includes the following:

```xml
<service name="replace_using_package_version" mode="buildtime">
  <param name="file">mariadb-setup.sh</param>
  <param name="regex">%%TAG%%</param>
  <param name="package">mariadb</param>
  <param name="parse-version">minor</param>
</service>
```

The service in this case would look for the `mariadb` package in the build
environment, get its version, and try to replace any occurrence of `%%TAG%%`
in the `mariadb-setup.sh` file with the `mariadb` package version.

In case the `mariadb` rpm package is not found within the build environment
it will also try to fecth the version from a `mariadb.obsinfo` file if any.
If no version can be determined the service fails.

`*.obsinfo` files are metadata files produced by the `obs_scm` service, which
is essentially used to retrieve sources from source repositories. This can be
useful for some corner cases in which the required package version is not part
of the build dependencies, this is likely to happen for helm chart builds.

The `file` parameter is optional and when omitted it will default to the
package's build recipe file, e.g. `Dockerfile` or `mariadb-image.kiwi`.

The `parse-version` could be skipped or if parameter's regular expression 
doesn't match then full package version is returned.

Possible `parse-version` values and it returned value in X.Y.Z.N version:

* `major`: `^(\d+)`, returns X
* `minor`: `^(\d+(\.\d+){0,1})`, returns X.Y
* `patch`: `^(\d+(\.\d+){0,2})`, returns X.Y.Z
* `patch_update`: `^(\d+(\.\d+){0,3})`, returns X.Y.Z.N
* `offset`: `^(?:\d+(?:\.\d+){0,3})[+-.~](?:git|svn|cvs)(\d+)`
  * returns X.Y.Z.N as it doesn't match
  * but if you have offset in your version X.Y.Z+git5 it returns 5
* `parse-version` is absent or parameter doesn't match, returns X.Y.Z.N

For instance, in this specific case, the service will apply the 
`^(\d+(\.\d+){0,1})` regular expression and use only the first match.
In case `mariadb` version was `10.3.4~git_r154` only the `10.3` part would be
used as the replacement string.

You could use this service multiple times in your `_service` file so `offset` 
parameter could be used in case you need more unique identification. 
For example %%TAG%%.%%OFFSET%% if you add another service with `regex` "%%OFFSET%%"
and `parse-version` "offset".

This service is mainly designed to work in `buildtime` mode, so it is applied
inside the build environment just before the start of the build.
