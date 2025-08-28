#!/usr/bin/env python3

import argparse
import enum
import glob
import logging
import re
import os
import shlex
import shutil
import sys
import traceback
from typing import Tuple

from osgbuild import fetch_sources
from osgbuild import git
from osgbuild import svn
from osgbuild import utils
from osgbuild.error import Error, UsageError

# Constants:
DEFAULT_UPSTREAM_ROOT = "/osgsw/upstream"
OLD_DEFAULT_UPSTREAM_ROOT = "/p/vdt/public/html/upstream"

# fmt: off
PROVIDER_PATTERNS = [
    (r'cbs\.centos\.org'               , 'cbs')    ,
    (r'centos\.org'                    , 'centos') ,
    (r'emisoft\.web\.cern\.ch'         , 'emi')    ,
    (r'fedoraproject\.org/pub/epel/'   , 'epel')   ,
    (r'fedoraproject\.org/pub/fedora/' , 'fedora') ,
    (r'globus\.org'                    , 'globus') ,
    (r'koji\.fedoraproject\.org/'      , 'fedora') ,
    (r'kojipkgs\.fedoraproject\.org/'  , 'fedora') ,
    (r'xrootd\.web\.cern\.ch/'         , 'xrootd') ]
# fmt: on


class ExtraAction(enum.Enum):
    NOTHING = "nothing"
    DIFF_SPEC = "diff_spec"
    EXTRACT_SPEC = "extract_spec"
    DIFF3_SPEC = "diff3_spec"
    UPDATE = "update"

    def __bool__(self):
        return self.value != "nothing"


class VcsType(enum.Enum):
    NONE = "none"
    SVN = "svn"
    GIT = "git"

    def __bool__(self):
        return self.value != "none"


def verify_rpm(srpm):
    """Verify that srpm is indeed an RPM. Raise Error if not."""
    cmd = ["rpm", "-qp", "--nomanifest", srpm]
    err = utils.unchecked_call(cmd)
    if err:
        raise Error("rpm: %s does not look like an RPM" % srpm)


def srpm_nv(srpm: str) -> Tuple[str, str]:
    """Return the NV (Name, Version) from an SRPM."""
    output, ret = utils.sbacktick(["rpm", "-qp", "--qf", "%{name} %{version}", srpm])
    if ret == 0:
        try:
            name, version = output.rstrip().split(" ")
            return name, version
        except ValueError:  # not enough/too many items
            pass
    raise Error("Unable to extract name and version from SRPM %s: %s" % (srpm, output))


def make_repo_subtree(
        srpm: str,
        url: str,
        sha1sum: str,
        dirname: str = "",
        extra_action: ExtraAction = ExtraAction.NOTHING,
        provider: str = "",
        vcs: VcsType = VcsType.NONE
):
    """
    Create a subtree in the packaging repo for the srpm and populate it as follows:
    $name/osg/*.spec        - the spec file as extracted from the srpm
                              (if extract_spec is True)
    $name/upstream/*.source - the location of the srpm under the upstream cache
                              as well as a comment describing where it's from

    Args:
        srpm: The path of the existing SRPM file to extract version information from
        url: The upstream URL the SRPM file was downloaded from
        sha1sum: the sha1sum of the SRPM
        dirname (optional): the subdirectory to create (otherwise,
            will use the SRPM's name)
        extra_action (optional): an extra action to perform after
            downloading the SRPM
        provider (optional): the name of the provider to use in the name of the
            .source file
        vcs (optional): what type of VCS (SVN or Git) operations to run
    """
    name, version = srpm_nv(srpm)
    if not dirname:
        dirname = name
    abs_srpm = os.path.abspath(srpm)

    package_dir = os.path.abspath(os.getcwd())
    if os.path.basename(package_dir) != dirname:
        package_dir = os.path.join(package_dir, dirname)

    if not os.path.exists(package_dir):
        if vcs == VcsType.SVN:
            utils.checked_call(["svn", "mkdir", package_dir])
        else:
            os.mkdir(package_dir)

    osg_dir = os.path.join(package_dir, "osg")
    if extra_action == ExtraAction.DIFF_SPEC:
        diff_spec(abs_srpm, osg_dir, want_diff3=False)
    elif extra_action == ExtraAction.EXTRACT_SPEC:
        extract_spec(abs_srpm, osg_dir, vcs)
    elif extra_action == ExtraAction.DIFF3_SPEC:
        if os.path.isdir(osg_dir):
            extract_orig_spec(osg_dir)
        diff_spec(abs_srpm, osg_dir, want_diff3=True)
    elif extra_action == ExtraAction.UPDATE:
        if os.path.isdir(osg_dir):
            logging.info("osg dir found -- doing 3-way diff")
            extract_orig_spec(osg_dir)
            diff_spec(abs_srpm, osg_dir, want_diff3=True)
        else:
            logging.info("osg dir not found -- updating .source file only")

    upstream_dir = os.path.join(package_dir, "upstream")

    if not os.path.exists(upstream_dir):
        if vcs == VcsType.SVN:
            utils.checked_call(["svn", "mkdir", upstream_dir])
        else:
            os.mkdir(upstream_dir)

    cached_filename = os.path.join(name, version, os.path.basename(srpm))

    make_source_file(
        url,
        cached_filename,
        upstream_dir,
        provider or get_provider(url),
        sha1sum,
        vcs,
    )

    if len(glob.glob(os.path.join(upstream_dir, "*.source"))) > 1:
        logging.info("More than one .source file found in upstream dir.")
        logging.info("Examine them to make sure there aren't duplicates.")


def get_provider(url: str) -> str:
    """
    Match the given url against the PROVIDER_PATTERNS and return the first one.
    """
    for provpat, provname in PROVIDER_PATTERNS:
        if re.search(provpat, url):
            return provname
    else:
        return "developer"


def make_source_file(
    url: str,
    cached_filename: str,
    upstream_dir: str,
    provider: str,
    sha1sum: str,
    vcs: VcsType = VcsType.NONE,
):
    """
    Create an upstream/*.source file with the appropriate name based
    on either `provider` or `url` if the former is not given.  Also add
    the new file to version control if possible.
    """
    source_filename = os.path.join(upstream_dir, provider+".srpm.source")
    source_contents = f"""\
{cached_filename} sha1sum={sha1sum}
# Downloaded from {url}
"""

    if os.path.exists(source_filename):
        logging.info("%s already exists. Backing it up as %s.old", source_filename, source_filename)
        shutil.move(source_filename, source_filename + ".old")
        utils.unslurp(source_filename, source_contents)
    else:
        utils.unslurp(source_filename, source_contents)
        if vcs == VcsType.SVN:
            svn_safe_add(source_filename)
        elif vcs == VcsType.GIT:
            utils.unchecked_call(["git", "add", "-N", source_filename])


def is_untracked_path(path):
    """Return True if the given path is untracked in SVN.
    Note: ignored files return False.
    """
    output, ret = utils.sbacktick(["svn", "status", path])

    return output.startswith('?')


def svn_safe_add(path):
    """Add path to SVN if it's not already in there."""
    if is_untracked_path(path):
        utils.unchecked_call(["svn", "add", path])


def get_spec_name_in_srpm(srpm):
    """Return the name of the spec file present in an SRPM.  Assumes
    there is exactly one spec file in the SRPM -- if there is more than
    one spec file, returns the name of the first one ``cpio'' prints.
    """
    out, ret = utils.sbacktick(
        "rpm2cpio %s | cpio -t '*.spec' 2> /dev/null" % shlex.quote(srpm),
        shell=True
    )
    if ret != 0:
        raise Error("Unable to get list of spec files from %s" % srpm)
    try:
        spec_name = [_f for _f in [x.strip() for x in out.split("\n")] if _f][0]
    except IndexError:
        spec_name = None

    if not spec_name:
        raise Error("No spec file inside %s" % srpm)

    return spec_name


def extract_from_rpm(rpm, file_or_pattern=None):
    """Extract a specific file or glob from an rpm."""
    command = "rpm2cpio " + shlex.quote(rpm) + " | cpio -ivd"
    if file_or_pattern:
        command += " " + shlex.quote(file_or_pattern)
    return utils.checked_call(command, shell=True)


def diff2(old_file, new_file, dest_file=None):
    """Do a 2-way diff, between `old_file` and `new_file`, where the
    differences are shown with markers like what SVN makes for a file
    with merge conflicts, e.g.:

    '''
    <<<<<<< old_file
    old stuff
    =======
    new stuff
    >>>>>>> new_file
    '''

    Write the result to `dest_file` if it is specified.
    Return the text of the diff on success, None on failure.
    """

    diff, ret = utils.sbacktick(["diff", """\
--changed-group-format=<<<<<<< %(old_file)s
%%<=======
%%>>>>>>>> %(new_file)s
""" % locals(), old_file, new_file])
    if not (ret == 0 or ret == 1):
        logging.warning("Error diffing %s %s: diff returned %d",
                        old_file, new_file, ret)
        return None

    if dest_file:
        utils.unslurp(dest_file, diff)
        logging.info("Difference between %s and %s written to %s",
                     old_file, new_file, dest_file)

    return diff


def diff3(old_file, orig_file, new_file, dest_file=None):
    """Do a 3-way diff between `old_file`, `orig_file`, and `new_file`,
    where the differences are shown with markers like what SVN makes
    for a file with merge conflicts, e.g.:

    '''
    <<<<<<< old_file
    old stuff
    ||||||| orig_file
    orig stuff
    =======
    new stuff
    >>>>>>> new_file
    '''

    Write the result to `dest_file` if it is specified.
    Return the text of the diff on success, None on failure.
    """

    diff, ret = utils.sbacktick(["diff3", "-m", old_file, orig_file, new_file])
    if not (ret == 0 or ret == 1):
        logging.warning("Error diffing %s %s %s: diff3 returned %d",
                        old_file, orig_file, new_file, ret)
        return None

    if dest_file:
        utils.unslurp(dest_file, diff)
        logging.info("Difference between %s, %s, and %s written to %s",
                     old_file, orig_file, new_file, dest_file)

    return diff


def diff_spec(srpm, osg_dir, want_diff3=False):
    """Do a 2- or 3-way diff between spec files found in the osg/
     directory, and the new upstream SRPM. If a 3-way diff is requested,
     also look at the spec file from the previous upstream SRPM. The
     osg/ directory must exist.

    The files that will be created or changed are:
    - $spec.old  : spec file from the osg/ dir before import
    - $spec.new  : spec file from the new upstream SRPM
    - $spec.orig : spec file from the old upstream SRPM (3-way only)
    - $spec      : combined spec file with differences separated by markers

    """
    if not os.path.isdir(osg_dir) or not glob.glob(os.path.join(osg_dir, '*')):
        logging.error("No osg/ dir found or no spec files in osg/ dir -- nothing to diff.")
        logging.error("To extract the spec file, run with -e instead.")
        sys.exit(1)

    with utils.chdir(osg_dir):
        srpm = os.path.abspath(srpm)

        spec_name = get_spec_name_in_srpm(srpm)
        spec_name_old = spec_name + ".old"
        spec_name_new = spec_name + ".new"

        if not os.path.exists(spec_name):
            logging.info("No old spec file matching %s - the spec file might have been renamed.",
                         spec_name)
            logging.info("Extracting new upstream spec file as %s", spec_name)
            extract_from_rpm(srpm, spec_name)
            return

        logging.info("OSG spec file found matching %s, saving to %s",
                     spec_name, spec_name_old)
        shutil.move(spec_name, spec_name_old)

        logging.info("Extracting new upstream spec file as %s", spec_name_new)
        extract_from_rpm(srpm, spec_name)
        shutil.move(spec_name, spec_name_new)

        if want_diff3:
            spec_name_orig = spec_name + ".orig"
            if os.path.exists(spec_name_orig):
                # Use `diff3 -m` to takes the changes that turn spec_name_orig into
                # spec_name_new, and applies these changes to spec_name_new.
                # Put the results into spec_name.

                diff3(spec_name_old, spec_name_orig, spec_name_new, spec_name)
            else:
                # This can happen if the package before import was an upstream
                # tarball with osg-provided spec file, as opposed to an
                # upstream SRPM with an osg-modified spec file.

                logging.info("No original upstream spec file matching %s - doing a two-way diff instead.", spec_name)
                diff2(spec_name_old, spec_name_new, spec_name)
        else:
            diff2(spec_name_old, spec_name_new, spec_name)


def extract_spec(srpm, osg_dir, vcs: VcsType = VcsType.NONE):
    """Extract the spec file from the SRPM, put it into an osg/ dir,
    and add both the osg/ dir and the spec file to SVN, if necessary.
    An existing spec file will be moved out of the way, with a .old
    extension, if necessary.
    """
    if not os.path.exists(osg_dir):
        os.mkdir(osg_dir)
        if vcs == VcsType.SVN:
            svn_safe_add(osg_dir)

    with utils.chdir(osg_dir):
        srpm = os.path.abspath(srpm)

        spec_name = get_spec_name_in_srpm(srpm)

        if os.path.exists(spec_name):
            spec_name_old = spec_name + ".old"
            logging.info("OSG spec file found matching %s, saving to %s",
                         spec_name, spec_name_old)
            shutil.move(spec_name, spec_name_old)

        logging.info("Extracting new upstream spec file as %s", spec_name)
        extract_from_rpm(srpm, spec_name)
        if vcs == VcsType.SVN:
            svn_safe_add(spec_name)
        elif vcs == VcsType.GIT:
            utils.unchecked_call(["git", "add", "-N", spec_name])


def extract_orig_spec(osg_dir):
    """Save a copy of the original upstream spec file from before the
    import into the osg_dir
    """
    with utils.chdir(osg_dir):
        utils.checked_call(['osg-build', 'prebuild', '..'])
        spec_paths = list(glob.glob("../_upstream_srpm_contents/*.spec"))
        for spec_path in spec_paths:
            spec_name_orig = os.path.basename(spec_path) + '.orig'
            logging.info("Saving original upstream spec file as %s",
                         spec_name_orig)
            shutil.copy(spec_path, spec_name_orig)


def move_to_cache(srpm: str, upstream_root: str):
    """Move the srpm to the upstream cache. Return the path to the file in the cache."""
    name, version = srpm_nv(srpm)
    base_srpm = os.path.basename(srpm)
    if not upstream_root:
        if os.path.isdir(DEFAULT_UPSTREAM_ROOT):
            upstream_dir = os.path.join(DEFAULT_UPSTREAM_ROOT, name, version)
        elif os.path.isdir(OLD_DEFAULT_UPSTREAM_ROOT):
            upstream_dir = os.path.join(OLD_DEFAULT_UPSTREAM_ROOT, name, version)
        else:
            raise Error(
                "Upstream root directory not found accessible; check that "
                "you're on a machine that has access to it or specify a "
                "different directory with the `-u` option."
            )
    else:
        upstream_dir = os.path.join(upstream_root, name, version)
    utils.safe_makedirs(upstream_dir)
    dest_file = os.path.join(upstream_dir, base_srpm)
    if os.path.exists(dest_file):
        os.unlink(dest_file)
    shutil.move(srpm, dest_file)

    return dest_file


def get_arguments(argv):
    parser = argparse.ArgumentParser(
        description="""\
This program should be called from a checkout of the packaging repo and given
the URL of an upstream SRPM. It will create and populate the appropriate
directories in the packaging repo as well as downloading and putting the SRPM
into the upstream cache."""
    )
    parser.add_argument(
        "-d",
        "--diff-spec",
        "-2",
        action="store_const",
        dest="extra_action",
        const=ExtraAction.DIFF_SPEC,
        help="Perform a two-way diff between the new upstream spec file and the OSG spec file. "
             "The new upstream spec file will be written to SPEC.new, and the OSG spec file will be "
             "written to SPEC.old; the differences will be written to SPEC. You will have to edit "
             "SPEC to resolve the differences.",
    )
    parser.add_argument(
        "--dirname", default=None,
        help="The directory name in the packaging repo the imported files will be placed into; "
             "defaults to the name of the package but you might want to change it "
             "to add an '.el9' suffix for example."
    )
    parser.add_argument(
        "-e", "--extract-spec", action="store_const", dest='extra_action', const=ExtraAction.EXTRACT_SPEC,
        help="Extract the spec file from the SRPM and put it into an osg/ subdirectory.")
    parser.add_argument(
        "--debug", action="store_const", dest="loglevel", const=logging.DEBUG,
        help="Print additional debugging messages."
    )
    parser.add_argument(
        "--no-vcs", action="store_false", dest="want_vcs",
        help="Do not perform version control system operations, only create files and directories."
    )
    parser.add_argument(
        "-o", "--output",
        help="The filename the upstream-url should be saved as.")
    parser.add_argument(
        "-p", "--provider",
        help="Who provided the SRPM being imported. For example, 'epel'. "
             "This is used to name the .source file in the 'upstream' directory. "
             "If unspecified, guess based on the URL, and use 'developer' as the fallback.")
    parser.add_argument(
        "-q", "--quiet", action="store_const", dest="loglevel", const=logging.WARNING,
        help="Print fewer messages."
    )
    parser.add_argument(
        "-3", "--diff3-spec", action="store_const", dest='extra_action', const=ExtraAction.DIFF3_SPEC,
        help="Perform a three-way diff between the original upstream spec file, the OSG spec file, "
             "and the new upstream spec file. These spec files will be written to SPEC.orig, "
             "SPEC.old, and SPEC.new, respectively; a merged result will be written to SPEC."
             "You will have to edit SPEC to resolve merge conflicts.")
    parser.add_argument(
        "-u", "--upstream", default=None,
        help="The base directory to put the upstream sources under."
    )
    parser.add_argument(
        "-U", "--update", action="store_const", dest='extra_action', const=ExtraAction.UPDATE,
        help="If there is an osg/ directory, do a 3-way diff like --diff3-spec.  Otherwise just update"
             " the .source file in the 'upstream' directory."
    )
    parser.add_argument("upstream_url", help="The URL of the upstream SRPM.")
    parser.set_defaults(extra_action=ExtraAction.NOTHING, loglevel=logging.INFO)
    args = parser.parse_args(argv[1:])
    return args, parser


def main(argv=None):
    if argv is None:
        argv = sys.argv

    args, parser = get_arguments(argv)
    try:
        logging.basicConfig(format=" >> %(message)s", level=args.loglevel)

        vcs = VcsType.NONE
        if args.want_vcs:
            if git.is_git("."):
                vcs = VcsType.GIT
            elif svn.is_svn("."):
                vcs = VcsType.SVN
            else:
                raise Error(
                    "No version control system detected in current directory. "
                    "Run this program from your checkout of a packaging repo, "
                    "or pass --no-vcs to skip version control operations."
                )

        if not re.match(r'(http|https|ftp):', args.upstream_url):
            raise UsageError("upstream-url is not a valid url")

        outfile = args.output or os.path.basename(args.upstream_url)
        sha1sum = fetch_sources.download_uri(args.upstream_url, outfile)
        verify_rpm(outfile)
        srpm = move_to_cache(outfile, args.upstream)
        make_repo_subtree(
            srpm,
            args.upstream_url,
            sha1sum,
            args.dirname,
            args.extra_action,
            args.provider,
            vcs,
        )

    except UsageError as e:
        parser.print_help()
        print(str(e), file=sys.stderr)
        return 2
    except SystemExit as e:
        return e.code
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 3
    except Error as e:
        logging.critical(str(e))
        logging.debug(e.traceback)
    except Exception as e:
        logging.critical("Unhandled exception: %s", e)
        logging.critical(traceback.format_exc())
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
