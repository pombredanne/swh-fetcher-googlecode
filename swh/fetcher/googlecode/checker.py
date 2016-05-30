# Copyright (C) 2015-2016  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

"""Namespace to deal with checks on git, svn and hg repository from
googlecode archives.

System requisites: svn, git, hg, unzip, pigz

"""

import glob
import logging
import os
import shutil
import tempfile

from subprocess import PIPE, Popen, check_call

from swh.core import config

from . import utils
from .fetcher import SWHGoogleArchiveFetcher


REPO_TYPE_FILENAME = 'project.json'
REPO_TYPE_KEY = 'repoType'
DEFAULT_SMALL_LENGTH_DISPATCH = 50 * 1024 * 1024  # 50 Mib
DEFAULT_MEDIUM_LENGTH_DISPATCH = 200 * 1024 * 1024  # 200 Mib


class SWHGoogleArchiveDispatchChecker(config.SWHConfig):
    """A google archive 'integrity' checker.

    This checker will:
    - check the archive's length
    - if not ok, refetch the archive
 .  - Depending on the archive's length, dispatch to other checker

    """
    def __init__(self):
        self.log = logging.getLogger(
            'swh.fetcher.google.SWHGoogleArchiveDispatchChecker')

    def process(self, archive_path, root_temp_dir):
        """Check the archive path is actually ok.

        """
        self.log.info('Check %s\'s metadata' % archive_path)

        extension = os.path.splitext(archive_path)[-1]
        if extension != '.gz' and extension != '.zip':
            self.log.warn('Skip %s. Only zip or gz extension files.' %
                          archive_path)
            return

        parent_dir = os.path.dirname(archive_path)
        # contains the repoType field
        project_json = os.path.join(parent_dir, REPO_TYPE_FILENAME)

        meta = utils.load_meta(project_json)
        if not meta:
            self.log.error('Skip %s. No project.json was detected.' %
                           archive_path)
            return

        repo_type = meta[REPO_TYPE_KEY]

        if repo_type == 'svn' and extension == '.zip':
            self.log.warn('Skip %s. Only svndump for svn type repository.' %
                          archive_path)
            return

        # check that the file's complete (some small numbers of files
        # fails because of it)
        json_meta = utils.load_meta(archive_path + '.json')
        length = os.path.getsize(archive_path)
        if length != int(json_meta['size']):  # somehow incomplete
            r = SWHGoogleArchiveFetcher().retrieve_source(archive_path,
                                                          json_meta,
                                                          archive_path)
            if not r:
                self.log.error('%s PROBLEM when fetching archive' %
                               archive_path)
                return

        from swh.scheduler.celery_backend.config import app
        from . import tasks  # noqa

        if length < DEFAULT_SMALL_LENGTH_DISPATCH:
            checker = app.tasks['swh.fetcher.googlecode.tasks.SWHGoogleSmallArchiveCheckerTask']  # noqa
        elif length < DEFAULT_MEDIUM_LENGTH_DISPATCH:
            checker = app.tasks['swh.fetcher.googlecode.tasks.SWHGoogleMediumArchiveCheckerTask']  # noqa
        else:
            checker = app.tasks['swh.fetcher.googlecode.tasks.SWHGoogleHugeArchiveCheckerTask']  # noqa

        checker.delay(archive_path, repo_type, root_temp_dir)


def basic_check(archive_path, temp_dir, cmd):
    """Execute basic integrity check.

    Args:
        archive_path: the full pathname to the archive to check
        temp_dir: the temporary directory to load and check the repository
        cmd: the actual command to check the repository is ok.

    Returns:
        True in case check is ok, False otherwise.

    """
    # all git and hg archives contain one folder with the project name
    cmd = ['unzip', '-q', '-o', archive_path, '-d', temp_dir]
    check_call(cmd)
    # Retrieve the archive content's first level folder (which cannot
    # be determined - in majority the name corresponds to the
    # project's name but not always...)
    repo_path = glob.glob(temp_dir + '/*')[0]

    with utils.cwd(repo_path):
        try:
            r = check_call(cmd)
            return r == 0
        except:
            return False


def check_svn_integrity(archive_path, temp_dir):
    """Check the repository's svn integrity.

    Args:
        archive_path: the full pathname to the archive to check
        temp_dir: the temporary directory to load and check the repository

    Returns:
        True in case check is ok, False otherwise.

    """
    project_name = os.path.basename(os.path.dirname(archive_path))
    repo_path = os.path.join(temp_dir, project_name)

    # create the repository that will be loaded with the dump
    cmd = ['svnadmin', 'create', repo_path]
    check_call(cmd)

    try:
        with Popen(['pigz', '-dc', archive_path], stdout=PIPE) as dump:
            cmd = ['svnadmin', 'load', '-q', repo_path]
            r = check_call(cmd, stdin=dump.stdout)
            return r == 0
    except:
        return False


def check_integrity(repo_type, archive_path, temp_dir):
    """Given a repository to uncompress in temp_dir with type repo_type,
       check its integrity.

    """
    if repo_type == 'git':
        return basic_check(archive_path, temp_dir, cmd=['git', 'fsck'])

    if repo_type == 'hg':
        return basic_check(archive_path, temp_dir, cmd=['hg', 'verify'])

    if repo_type == 'svn':
        return check_svn_integrity(archive_path, temp_dir)

    raise NotImplemented("Repository type %s not implemented." % repo_type)


class SWHGoogleArchiveChecker(config.SWHConfig):
    """A google archive 'integrity' checker.

    This checker will:

    - determine the archive's nature (hg, git, svn) by checking the
      project.json associated file
    - uncompress the archive on a temporary folder
    - depending on its nature, check that the archive's integrity is ok
      - git: `git fsck`
      - svn: `pigz -dc foo-repo.svndump.gz | svnadmin load repos/foo-repo`
      - hg:  `hg verify`

    """
    def __init__(self):
        self.log = logging.getLogger(
            'swh.fetcher.google.SWHGoogleArchiveChecker')

    def process(self, archive_path, repo_type, root_temp_dir):
        """Check the archive path is actually ok.

        """
        self.log.info('Check %s\'s metadata' % archive_path)

        try:
            # compute the repo path repository once uncompressed
            temp_dir = tempfile.mkdtemp(suffix='.swh.fetcher.googlecode',
                                        prefix='tmp.',
                                        dir=root_temp_dir)

            self.log.debug('type: %s, archive: %s' % (repo_type, archive_path))

            if check_integrity(repo_type, archive_path, temp_dir):
                self.log.info('%s SUCCESS' % archive_path)
            else:  # we'll check that the current file is complete
                self.log.error('%s FAILURE' % archive_path)
        except Exception as e:
            self.log.error('%s PROBLEM with archive - %s' %
                           (archive_path, e))
        finally:
            # cleanup the temporary directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
