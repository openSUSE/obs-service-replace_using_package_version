.PHONY: test

python_lookup_name = python
python = $(shell which $(python_lookup_name))
version := $(shell $(python) -c \
    'from replaceUsingPackageVersion.version import __version__; print(__version__)')
dashes_line = \
    -------------------------------------------------------------------
changes_head = ${dashes_line}%n%cd - %ae%n%n

flake:
	tox -e check

build: clean tox
	# build the sdist source tarball
	$(python) ./setup.py sdist
	# provide rpm changelog from git changelog
	git log --pretty=format:"${changes_head}%w(77)- %s %n%w(77,4,4)%b" \
        --date=format:"%a %b %d %T %Z %Y" --no-merges \
        >> dist/obs-service-replace_using_package_version.changes
	# update package version in spec file
	cat rpm/obs-service-replace_using_package_version-spec-template | \
        sed -e s'/__VERSION__/${version}/' > \
        dist/obs-service-replace_using_package_version.spec

clean:
	rm -rf dist
	rm -rf build

tox:
	tox
