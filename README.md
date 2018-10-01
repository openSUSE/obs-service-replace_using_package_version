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
</service>
```

The service in this case would look for the `mariadb` in the build environment,
get the version of the package, and try to replace any occurrence of `%%TAG%%`
in `mariadb-imgae.kiwi` file with the `mariadb` package version.

This service is mainly designed to work in `buildtime` mode, so it is applied
inside the build environment just before the start of the build.
