import dataclasses
import enum
import re
import typing as t


class RestrictedTarget:
    """
    RestrictedTarget defines a set of Koji targets that have restrictions on
    which branches or remotes you can use as sources for (non-scratch) builds.

    The attributes are:
    - name: used for reference
    - remotes: a list of Git remote names (see the REMOTES constant) that are
        allowed to build into this target.  (SVN is handled separately.)
    - subtree_branch_re: a regexp of subtrees that you are allowed to build
        into this target from.  A subtree is the parent directory of each
        package, so "24-main/xrootd" will have the subtree of "24-main".
        This is used in Git repos with the "subtree" layout and SVN.
        Not used for Git repos with the "legacy" layout, where each package
        dir is directly under the top level of the repo.
    - git_branch_re: a regexp of Git branches that you are allowed to build
        into this target from.  This is for Git repos with the "legacy"
        layout, where each package dir is directly under the top level of the
        repo; note that the pattern should match remote branches
        (e.g. "origin/master") as well.
    """
    remotes: t.List[str]
    koji_target_re: re.Pattern
    subtree_branch_re: t.Optional[re.Pattern] = None
    git_branch_re: re.Pattern = None

    def __init__(
            self,
            name: str,
            remotes: t.Union[str, t.List[str]],
            koji_target_re: t.Union[str, re.Pattern],
            subtree_branch_re: t.Union[str, re.Pattern] = None,
            git_branch_re: t.Union[str, re.Pattern] = None,
    ):
        self.name = name

        #
        # Compile any regexps that are provided as strings.
        #
        if isinstance(koji_target_re, str):
            self.koji_target_re = re.compile(koji_target_re)
        elif isinstance(koji_target_re, re.Pattern):
            self.koji_target_re = koji_target_re
        else:
            raise TypeError("koji_target_re has the wrong type: %s" % type(koji_target_re))

        if not subtree_branch_re:
            self.subtree_branch_re = None
        elif isinstance(subtree_branch_re, str):
            self.subtree_branch_re = re.compile(subtree_branch_re)
        elif isinstance(subtree_branch_re, re.Pattern):
            self.subtree_branch_re = subtree_branch_re
        else:
            raise TypeError("subtree_branch_re has the wrong type: %s" % type(subtree_branch_re))

        if isinstance(git_branch_re, str):
            self.git_branch_re = re.compile(git_branch_re)
        elif isinstance(git_branch_re, re.Pattern):
            self.git_branch_re = git_branch_re
        else:
            raise TypeError("git_branch_re has the wrong type: %s" % type(git_branch_re))

        # The list of remotes you can build from; if only one is given, make sure we store it as a list.
        if not remotes:
            raise ValueError("remotes must contain at least one remote")
        if isinstance(remotes, str):
            self.remotes = [remotes]
        else:
            self.remotes = remotes



# The original patterns are here for reference.  Note that the new patterns are not anchored.
# Use re.fullmatch() or re.match() if you want to anchor them
# SVN branches implicitly start with 'branches/'

# KOJI_RESTRICTED_TARGETS = {
#     r'^osg-(el\d+)$'                                : 'main',
#     r'^osg-(?P<osgver>[0-9.]+)-upcoming-(el\d+)$'   : 'upcoming',
#     r'^devops-(el\d+)$'                             : 'devops',
#     r'^osg-(el\d+)-internal$'                       : 'oldinternal',
#     r'^osg-(?P<osgver>\d+\.\d+)-(el\d+)$'           : 'versioned',
#     r'^osg-(?P<osgver>[0-9.]+)-main-(el\d+)$'       : 'versioned',
#     r'^osg-(?P<osgver>[0-9.]+)-internal-(el\d+)$'   : 'internal',
#     r'^chtc-(el\d+)$'                               : 'chtc',
# }
# GIT_RESTRICTED_BRANCHES = {
#     r'^(\w*/)?(?P<osgver>[0-9.]+)-upcoming$'    : 'upcoming',
#     r'^(\w*/)?internal$'                        : 'oldinternal',
#     r'^(\w*/)?devops$'                          : 'devops',
#     r'^(\w*/)?osg-(?P<osgver>\d+\.\d+)$'        : 'versioned',
#     r'^(\w*/)?(?P<osgver>[0-9.]+)-main$'        : 'versioned',
#     r'^(\w*/)?(?P<osgver>[0-9.]+)-internal$'    : 'internal',
# }

# fmt: off


# These are the definitions of restricted targets.
RESTRICTED_TARGETS = {
    #
    # Targets currently used by OSG
    #

    # Upcoming, e.g. "24-upcoming", which is built with Koji targets with names
    # like "osg-24-upcoming-el8"
    "upcoming": RestrictedTarget(
        name="upcoming",
        remotes=["osg", "osg2"],
        koji_target_re      =        r'osg-(?P<osgver>[0-9.]+)-upcoming-(el\d+)',
        subtree_branch_re   =            r'(?P<osgver>[0-9.]+)-upcoming',
        git_branch_re       =     r'(\w*/)?(?P<osgver>[0-9.]+)-upcoming',
    ),

    # Main, e.g. "24-main", which is built with Koji targets with names
    # like "osg-24-main-el8"
    "newmain": RestrictedTarget(  # XXX rename to 'main' after I've gotten rid of the osg-elX targets
        name="newmain",
        remotes=["osg", "osg2"],
        koji_target_re      =        r'osg-(?P<osgver>[0-9.]+)-main-(el\d+)',
        subtree_branch_re   =            r'(?P<osgver>[0-9.]+)-main',
        git_branch_re       =     r'(\w*/)?(?P<osgver>[0-9.]+)-main',
    ),

    # Versioned internal, e.g. 24-internal, which is built with Koji targets
    # with names like "osg-24-internal-el8".
    "internal": RestrictedTarget(
        name="internal",
        remotes=["osg", "osg2"],
        koji_target_re      =        r'osg-(?P<osgver>[0-9.]+)-internal-(el\d+)',
        subtree_branch_re   =            r'(?P<osgver>[0-9.]+)-internal',
        git_branch_re       =     r'(\w*/)?(?P<osgver>[0-9.]+)-internal',
    ),

    #
    # Targets used outside of OSG Software
    #
    "chtc": RestrictedTarget(
        name="chtc",
        remotes=["chtc"],
        koji_target_re      = r'chtc-(el\d+)',
        git_branch_re       = r'.*',
    ),
    "hcc": RestrictedTarget(
        name="hcc",
        remotes=["hcc"],
        koji_target_re      = r'hcc-(el\d+)',
        git_branch_re       = r'.*',
    ),

    #
    # Past, deprecated OSG Software targets.
    #

    # The deprecated "osg-internal" branch, which is built into Koji targets with names
    # like "osg-el7-internal".
    "oldinternal": RestrictedTarget(
        name="oldinternal",
        remotes=["osg", "osg2"],
        koji_target_re      =  r'osg-(el\d+)-internal',
        subtree_branch_re   =          r'osg-internal',
        git_branch_re       =       r'(\w*/)?internal',
    ),
    # The deprecated "devops" branch, which is built into Koji targets with names
    # like "devops-el7".
    "devops": RestrictedTarget(
        name="devops",
        remotes=["osg", "osg2"],
        koji_target_re      =          r'devops-(el\d+)',
        subtree_branch_re   =          r'devops',
        git_branch_re       =   r'(\w*/)?devops',
    ),
    # The versioned OSG branches, e.g. osg-3.5, osg-3.6, etc., built into Koji
    # targets with names like "osg-3.6-el7".
    "versioned": RestrictedTarget(
        name="versioned",
        remotes=["osg", "osg2"],
        koji_target_re      =          r'osg-(?P<osgver>\d+\.\d+)-(el\d+)',
        subtree_branch_re   =          r'osg-(?P<osgver>\d+\.\d+)',
        git_branch_re       =   r'(\w*/)?osg-(?P<osgver>\d+\.\d+)',
    ),
}

# fmt: on

class RemoteLayout(enum.Enum):
    """
    RemoteLayout is for the two types of Git repo layout:
    - LEGACY: Each package directory is directly under the top of the tree.
        Target protection rules match against the Git branch.
    - SUBTREE: Package directories are one level down from the tree.
        Target protection rules match against the parent of the package
        directory.
    """
    LEGACY = "legacy"
    SUBTREE = "subtree"


@dataclasses.dataclass
class GitHubRemoteType:
    """
    A remote that defines a GitHub repo.  The attributes are:

    - name: a symbolic name of the remote, referenced in the RESTRICTED_TARGETS
        constant.
    - layout: how the Git repo is laid out.
    - repo: the "organization/repo" string of the GitHub repo.
    """
    name: str  # TODO This feels hacky
    repo: str
    layout: RemoteLayout

    @property
    def unauth(self):
        """
        The URL that can be used for cloning the repo without authentication.
        """
        return f"https://github.com/{self.repo}"

    @property
    def auth(self):
        """
        The URL that requires authentication and can be used for pushing to the repo.
        """
        return f"git@github.com:{self.repo}"

    @property
    def urls(self):
        return [self.auth, self.unauth]

    @property
    def remote_map(self) -> t.Dict[str, str]:
        """
        Map the authenticated URL to an anonymous checkout URL.
        """
        return {self.auth: self.unauth}


# These are the definitions of the 'known' remotes. The names are used by the
# RESTRICTED_TARGETS constant.
REMOTES = {
    "osg": GitHubRemoteType(
        name="osg",
        repo="opensciencegrid/Software-Redhat.git",
        layout=RemoteLayout.LEGACY,
    ),
    "hcc": GitHubRemoteType(
        name="hcc",
        repo="unlhcc/hcc-packaging.git",
        layout=RemoteLayout.LEGACY,
    ),
    "chtc": GitHubRemoteType(
        name="chtc",
        repo="CHTC/packaging.git",
        layout=RemoteLayout.LEGACY,
    ),
    "osg2": GitHubRemoteType(
        name="osg2",
        repo="osg-htc/software-packaging.git",
        layout=RemoteLayout.SUBTREE,
    ),
}

