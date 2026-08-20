#
# TODO  This spec file is not used much anymore since we stopped building
#       osg-build RPMs. I'm keeping it around as a reference for the
#       dependencies and as a way to store the changelog; both these things
#       should be split out and the spec file removed.
#
#global betatag .pre
%global _release 1

Name:           osg-build
Version:        2.3.0
Release:        %{?betatag:0.}%{_release}%{?betatag}%{?dist}
Summary:        Build tools for the OSG

License:        Apache 2.0
URL:            https://github.com/osg-htc/osg-build

Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch

Requires:       %{name}-base = %{version}
Requires:       %{name}-mock = %{version}
Requires:       %{name}-koji = %{version}

BuildRequires: python3
%define __python /usr/bin/python3

BuildRequires:       git-core


%description
%{summary}
See %{url} for details.


%package base
Requires:       git-core
Requires:       rpm-build
# quilt is not (yet) available on EL10
Recommends:     quilt
Requires:       rpmlint
Requires:       subversion
Requires:       wget
Requires:       epel-rpm-macros
Summary:        OSG-Build base package, not containing mock or koji modules or koji-based tools

%description base
%{summary}
Installing this package makes osg-build and osg-import-srpm
available. osg-build can do rpmbuilds and run the lint and quilt
tasks. osg-build-mock is required to use the mock task, and
osg-build-koji is required to use the koji task.


%package mock
Requires:       %{name}-base = %{version}
# mock 2.0 attempts to build with dnf inside the chroot which fails miserably.
# Fixed in 2.1 but EL 6 doesn't have that.
Requires:       mock >= 2.1
Summary:        OSG-Build Mock plugin, allows builds with mock

%description mock
%{summary}


%package koji
Requires:       %{name}-base = %{version}
Requires:       openssl
Requires:       koji >= 1.33.0
Requires:       krb5-workstation
Summary:        OSG-Build Koji plugin and Koji-based tools

%description koji
%{summary}
Installing this package enables the 'koji' task in osg-build and adds
the following tools:
- koji-blame
- koji-tag-diff
- osg-koji
- osg-promote


%package tests
Requires:       %{name} = %{version}
Provides:       %{name}-test = %{version}
Summary:        OSG-Build tests

%description tests
%{summary}


%prep
%setup -q -n %{name}-%{version}

%install
find . -type f -exec sed -ri '1s,^#!/usr/bin/env python,#!%{__python},' '{}' +
make install DESTDIR=$RPM_BUILD_ROOT PYTHON=%{__python}
rm -f $RPM_BUILD_ROOT/%{_bindir}/sha1vdt
# ^ this script is useless unless AFS is available

%check
SW_VERSION=$(%{__python} -c "import sys; sys.path.insert(0, '.'); from osgbuild import version; sys.stdout.write(version.__version__ + '\n')")
if [[ $SW_VERSION != %{version} ]]; then
    echo "Version mismatch between RPM version (%{version}) and software version ($SW_VERSION)"
    echo "Edit osgbuild/version.py"
    exit 1
fi



%files

%files tests
%{_bindir}/osg-build-test
%dir %{python_sitelib}/osgbuild/test
%{python_sitelib}/osgbuild/test/*.py*
%{python_sitelib}/osgbuild/test/__pycache__

%files base
%{_bindir}/%{name}
%{_bindir}/osg-import-srpm
%dir %{python_sitelib}/osgbuild
%{python_sitelib}/osgbuild/__init__.py*
%{python_sitelib}/osgbuild/constants.py*
%{python_sitelib}/osgbuild/error.py*
%{python_sitelib}/osgbuild/fetch_sources.py*
%{python_sitelib}/osgbuild/git.py*
%{python_sitelib}/osgbuild/importer.py*
%{python_sitelib}/osgbuild/main.py*
%{python_sitelib}/osgbuild/srpm.py*
%{python_sitelib}/osgbuild/svn.py*
%{python_sitelib}/osgbuild/target_protection.py*
%{python_sitelib}/osgbuild/utils.py*
%{python_sitelib}/osgbuild/version.py*
%{_datadir}/%{name}/rpmlint.cfg
%{python_sitelib}/osgbuild/__pycache__

%files mock
%{python_sitelib}/osgbuild/mock.py*

%files koji
%{_bindir}/koji-blame
%{_bindir}/koji-tag-diff
%{_bindir}/osg-koji
%{_bindir}/osg-promote
%{python_sitelib}/osgbuild/clientcert.py*
%{python_sitelib}/osgbuild/kojiinter.py*
%{python_sitelib}/osgbuild/promoter.py*
%{_datadir}/%{name}/osg-koji.conf.in
%{_datadir}/%{name}/promoter.ini
