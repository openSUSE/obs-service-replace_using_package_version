# obs-service-replace_using_package_version
An OBS service to replace a regex with some package version available
in the build time environment or repositories.

This service makes sense mostly in `buildtime` mode.

Travis CI: [![Build Status](https://travis-ci.org/davidcassany/obs-service-replace_using_package_version.svg?branch=master)](https://travis-ci.org/davidcassany/obs-service-replace_using_package_version)

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
