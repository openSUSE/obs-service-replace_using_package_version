# obs-service-replace_using_package_version
An OBS service to replace a regex with some package version available
in the build time environment or repositories.

This service makes sense mostly in `buildtime` mode.

Travis CI: [![Build Status](https://travis-ci.org/openSUSE/obs-service-replace_using_package_version.svg?branch=master)](https://travis-ci.org/openSUSE/obs-service-replace_using_package_version)

## Development

This is a python project that makes use of setuptools and virtual environment.

To set the development environment consider the following commands:

```bash
# Get into the repository folder
$ cd obs-service-replace_using_package_version

# Initiate the python3 virtualenv
$ python3 -m venv .env3

# Activate the virutalenv
$ source .env3/bin/activate

# Install development dependencies
$ pip install -r requirements.txt

# Run tests and code style checks
$ tox
```

## Usage

Consider a `_service` file that includes the following:

```xml
<service name="replace_using_package_version" mode="buildtime">
  <param name="file">mariadb-image.kiwi</param>
  <param name="regex">%%TAG%%</param>
  <param name="package">mariadb</param>
  <param name="parse-version">minor</param>
</service>
```

The service in this case would look for the `mariadb` package in the build
environment, get its version, and try to replace any occurrence of `%%TAG%%`
in `mariadb-imgae.kiwi` file with the `mariadb` package version.

The `parse-version` states to use only up to the minor version part for a given
versio string. For instance, in this specific case, the service will
apply the `^(\d+(\.\d+){0,1})` regular expression and use only the first match.
In case `mariadb` version was `10.3.4~git_r154` only the `10.3` part would be
used as the replacement string.

This service is mainly designed to work in `buildtime` mode, so it is applied
inside the build environment just before the start of the build.
