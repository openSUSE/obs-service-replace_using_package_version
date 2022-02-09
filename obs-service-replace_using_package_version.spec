#
# spec file for package obs-service-replace_with_package_version
#
# Copyright (c) 2022 SUSE LLC
# Copyright (c) 2018 SUSE LINUX GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via https://bugs.opensuse.org/
#
%define service replace_using_package_version

Name:           obs-service-%{service}
Version:        0.0.3
Release:        0
Summary:        An OBS service: Replaces a regex with the version value of a package
License:        GPL-3.0-or-later
Url:            https://github.com/openSUSE/obs-service-%{service}
Source0:        replace_using_package_version.py
Source1:        replace_using_package_version.service
Source2:        LICENSE
BuildRequires:  python3-setuptools
Requires:       python3-setuptools
Requires:       python3-docopt
BuildArch:      noarch

%description
This service replaces a given regex with the version value of
a given package. Can be used to align the version of you package or image
to the version of another package.

%prep
# for %%license to work
cp %{SOURCE2} .

%build

%install
install -Dpm 0755 %{SOURCE0} %{buildroot}%{_prefix}/lib/obs/service/%{service}
install -Dpm 0755 %{SOURCE1} %{buildroot}%{_prefix}/lib/obs/service/

%files
%dir %{_prefix}/lib/obs
%dir %{_prefix}/lib/obs/service
%{_prefix}/lib/obs/service
%license LICENSE

%changelog
