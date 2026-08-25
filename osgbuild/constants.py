"""Global constants for osg-build"""
import os as _os

WD_RESULTS = '_build_results'
WD_PREBUILD = '_final_srpm_contents'
WD_UNPACKED = '_upstream_srpm_contents'
WD_UNPACKED_TARBALL = '_upstream_tarball_contents'
WD_QUILT = '_quilt'
BACKUP_WEB_CACHE_PREFIX = 'https://vdt.cs.wisc.edu/upstream'
WEB_CACHE_PREFIX = 'https://sw-upstream.svc.osg-htc.org/upstream'

KOJI_USER_CONFIG_DIR = _os.path.expanduser("~/.koji")
OSG_KOJI_USER_CONFIG_DIR = _os.path.expanduser("~/.osg-koji")
KOJI_CLIENT_CERT = _os.path.join(OSG_KOJI_USER_CONFIG_DIR, "client.crt")

DATA_DIR = "/usr/share/osg-build"
PROMOTER_INI = 'promoter.ini'
SIGNING_KEYS_INI = 'signing_keys.ini'
DEFAULT_AUTHTYPE = "kerberos"
LOCAL_KOJI_INI = "koji.ini"

KOJI_HUB = "https://koji.osg-htc.org"
KOJI_WEB = "https://koji.osg-htc.org"

DEFAULT_BUILDOPTS_COMMON = {
    'background': False,
    'cache_prefix': None,
    'dry_run': False,
    'full_extract': False,
    'getfiles': False,
    'koji_backend': None,
    'mock_clean': True,
    'mock_config': None,
    'mock_config_from_koji': None,
    'no_wait': False,
    'regen_repos': False,
    'repo': None,
    'scratch': False,
    'target_arch': None,
    'working_directory': '.',
}

DVERS = ['el7', 'el8', 'el9', 'el10']
CHTC_DVERS = ['el9']
OSG_3_5_DVERS = ['el7', 'el8']
OSG_3_6_DVERS = ['el7', 'el8', 'el9']
OSG_23_DVERS = ['el8', 'el9']
OSG_24_DVERS = ['el8', 'el9']
OSG_25_DVERS = ['el8', 'el9', 'el10']
OSG_26_DVERS = ['el8', 'el9', 'el10']

DEFAULT_BUILDOPTS_BY_DVER = {}
for _dver in DVERS:
    DEFAULT_BUILDOPTS_BY_DVER[_dver] = dict(
        distro_tag='osg.'+_dver,
        koji_tag=None,
        koji_target=None,
        redhat_release=_dver[2:]
    )
DEFAULT_BUILDOPTS_BY_DVER['el7']['_binary_payload'] = 'w2.xzdio'

# If the dver on the current machine can't be detected for some reason, or
# isn't EL, use this.
FALLBACK_DVER = 'el9'
DEFAULT_DVERS = ['el8', 'el9']
DEFAULT_DVERS_BY_REPO = {
    '3.5': OSG_3_5_DVERS,
    'osg-3.5': OSG_3_5_DVERS,
    '3.5-upcoming': OSG_3_5_DVERS,

    '3.6': OSG_3_6_DVERS,
    'osg-3.6': OSG_3_6_DVERS,
    '3.6-upcoming': OSG_3_6_DVERS,
    'devops': OSG_3_6_DVERS,

    '23-main': OSG_23_DVERS,
    '23-upcoming': OSG_23_DVERS,
    '23-internal': OSG_23_DVERS,
    '23-empty': OSG_23_DVERS,
    '23-contrib': OSG_23_DVERS,

    '24-main': OSG_24_DVERS,
    '24-upcoming': OSG_24_DVERS,
    '24-internal': OSG_24_DVERS,
    '24-empty': OSG_24_DVERS,
    '24-contrib': OSG_24_DVERS,

    '25-main': OSG_25_DVERS,
    '25-upcoming': OSG_25_DVERS,
    '25-internal': OSG_25_DVERS,
    '25-empty': OSG_25_DVERS,
    '25-contrib': OSG_25_DVERS,

    '26-main': OSG_26_DVERS,
    '26-upcoming': OSG_26_DVERS,
    '26-internal': OSG_26_DVERS,
    '26-empty': OSG_26_DVERS,
    '26-contrib': OSG_26_DVERS,

    'chtc': CHTC_DVERS,
}

REPO_HINTS_STATIC = {
    'devops': {'target': 'devops-%(dver)s', 'tag': 'osg-%(dver)s'},
    'hcc': {'target': 'hcc-%(dver)s', 'tag': 'hcc-%(dver)s'},
    'chtc': {'target': 'chtc-%(dver)s', 'tag': 'chtc-%(dver)s'},
}

BUGREPORT_EMAIL = "help@osg-htc.org"

BACKGROUND_THRESHOLD = 5
