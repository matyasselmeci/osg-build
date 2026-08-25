Changelog
=========

This is the changelog of the V2-branch of the OSG Build Tools.

## 2.3.0 - 2026-08-20

_This is the first release with support for OSG 26._

### Added

- Add support for OSG 26


## 2.2.1 - 2025-10-29

### Fixed

- Fix EL8 compatibility issue due to use of `re.Pattern` ([SOFTWARE-6244](https://opensciencegrid.atlassian.net/browse/SOFTWARE-6244))


## 2.2.0 - 2025-09-30

### Added

- Add `--debug-xmlrpc` flag to debug Koji XMLRPC calls
- Add promotion routes for 24-contrib and 24-empty ([SOFTWARE-5970](https://opensciencegrid.atlassian.net/browse/SOFTWARE-5970))

### Removed

- Remove OSG 24 EL10 promotion routes


## 2.1.1 - 2025-09-11

### Fixed

- Fix missing `DEFAULT_DVERS_BY_REPO` entry for the `*-empty` and `*-contrib` repos


## 2.1.0 - 2025-09-05

_This is the first release with support for OSG 25._

### Changed

- Request a Kerberos ticket if necessary before making Koji builds

### Added

- Add support for OSG 25


## 2.0.0 - 2025-07-15

_This is the first release with support for EL10._

### Changed

- Determine `--repo` based on a "koji.ini" file from the branch directory in Koji builds ([SOFTWARE-6066](https://opensciencegrid.atlassian.net/browse/SOFTWARE-6066))

### Added

- Add support for building from https://github.com/osg-htc/software-packaging.git ([SOFTWARE-6078](https://opensciencegrid.atlassian.net/browse/SOFTWARE-6078))
- Add support for EL10 ([SOFTWARE-6165](https://opensciencegrid.atlassian.net/browse/SOFTWARE-6165))


## 1.99.5 - 2025-05-06

### Changed

- Download upstream sources from the new server https://sw-upstream.svc.osg-htc.org, falling back to https://vdt.cs.wisc.edu on failure (SOFTWARE-6106)
- Koji builds now require specifying the target with --repo or --koji-target

### Added
- Add ability to make "variant" packages by adding some suffix starting with `__` to the package directory

### Removed

- Drop the "AFS cache prefix" -- upstream sources are always downloaded via HTTP(S), even if AFS is locally mounted
- Remove the `--autoclean` and `--no-autoclean` args -- old dirs are always cleaned up on a run
- Disable the `--3.5-upcoming` and `--3.6-upcoming` args

### Fixed

- Don't specify a --tag when git cloning from HEAD


## 1.99.4 - 2025-01-03

### Added

- Add support for submodules in .source files

### Fixed

- Fix reversed test when asking for confirmation with out-of-date working directories


## 1.99.3 - 2024-09-25

_This is the first version with OSG 24 support and support for the CHTC repos._

### Changed

- Double the signing timeout in osg-sign to give us more time for multiple arches

### Added

- Add `--repo-list` command for listing the valid values for `--repo`
- Add support for OSG 24 ([SOFTWARE-5960](https://opensciencegrid.atlassian.net/browse/SOFTWARE-5960))
- Add repo hints for `*-empty` and `*-contrib` repos (Matthew Westphall)
- Add support for CHTC repos ([INF-1662](https://opensciencegrid.atlassian.net/browse/INF-1662))

### Removed

- Do not list valid values for `--repo` in `--help`
- Drop printing tables in old Jira syntax


## 1.99.2 - 2023-10-19

### Changed

- Make OSG Build Tools pip installable

### Added

- Package signing script `osg-sign` ([SOFTWARE-5637](https://opensciencegrid.atlassian.net/browse/SOFTWARE-5637))


## 1.99.1 - 2023-10-12

### Added

- Add Kerberos support ([SOFTWARE-5696](https://opensciencegrid.atlassian.net/browse/SOFTWARE-5696))

### Fixed

- Fix koji-blame not working with Koji CLI 1.24+ by using `list-history` instead of `list-tag-history` ([SOFTWARE-4532](https://opensciencegrid.atlassian.net/browse/SOFTWARE-4532))


## 1.99.0 - 2023-09-29

### Changed

- Make OSG 3.6 the default target release series ([SOFTWARE-5208](https://opensciencegrid.atlassian.net/browse/SOFTWARE-5208))
- Combine `osg-koji-site.conf` and `osg-koji-home.conf` into `osg-koji.conf`
- Chop off `.elX` suffix from package directories before running `koji add-pkg` ([SOFTWARE-5502](https://opensciencegrid.atlassian.net/browse/SOFTWARE-5502))

### Added

- Allow building from git branches and add branch protection ([SOFTWARE-5476](https://opensciencegrid.atlassian.net/browse/SOFTWARE-5476))
- Add support for OSG 23 ([SOFTWARE-5622](https://opensciencegrid.atlassian.net/browse/SOFTWARE-5622))

### Removed

- Drop el6 and pre-3.5 promotion routes
- Drop unversioned `--upcoming` flag and repos
- Drop support for building into 'trunk' and unversioned 'upcoming'
- Drop promotion routes for 3.5 and unversioned upcoming


## Older versions

Older changes are in the [osg-build.spec file in V1-branch](https://github.com/osg-htc/osg-build/blob/V1-branch/rpm/osg-build.spec).
