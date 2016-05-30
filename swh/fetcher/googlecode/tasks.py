# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.scheduler.task import Task
from .fetcher import SWHGoogleArchiveFetcher
from .checker import SWHGoogleArchiveChecker, SWHGoogleArchiveDispatchChecker


class SWHGoogleArchiveFetcherTask(Task):
    """Main task to fetch and check archive source from google code
       archive server.

       The checks are made on:
       - size
       - md5
       from the associated '.json' file associated to the archive fetched.

    """
    task_queue = 'swh_fetcher_googlecode_fetch_archive'

    def run(self, archive_gs, destination_rootpath):
        SWHGoogleArchiveFetcher().process(archive_gs, destination_rootpath)


class SWHGoogleArchiveDispatchCheckerTask(Task):
    """Main task to check fetched archive files from google code archive
       server.

       Check the length of the archives.
       If archive's length is not ok, refetch it.
       When done, depending on its size, dispatch:
       - large: to SWHGoogleArchiveCheckerHugeTask
       - small: to SWHGoogleArchiveCheckerSmallTask
       - uncompress the archive on a temporary folder
       - integrity check according to repo's nature (git, hg, svn)

    """
    task_queue = 'swh_fetcher_googlecode_dispatch_check_archive'

    def run(self, path, root_temp_dir):
        SWHGoogleArchiveDispatchChecker().process(path, root_temp_dir)


class SWHGoogleArchiveCheckerTask(Task):
    """Main task to check huge fetched archive files from google code
    archive server.

    The checks are more thorough, that is:
    - uncompress the archive on a temporary folder
    - integrity check according to repo's nature (git, hg, svn)

    Intended to be inherited (cf. SWHGoogleSmallArchiveCheckerTask,
    SWHGoogleMediumArchiveCheckerTask,
    SWHGoogleHugeArchiveCheckerTask)

    """
    def run(self, archive_path, repo_type, root_temp_dir):
        """Process a repo archive archive_path of type repo_type.
        The archive is uncompressed in root_temp_dir.

        """
        SWHGoogleArchiveChecker().process(
            archive_path,
            repo_type,
            root_temp_dir)


class SWHGoogleSmallArchiveCheckerTask(SWHGoogleArchiveCheckerTask):
    task_queue = 'swh_fetcher_googlecode_check_small_archive'


class SWHGoogleMediumArchiveCheckerTask(SWHGoogleArchiveCheckerTask):
    task_queue = 'swh_fetcher_googlecode_check_medium_archive'


class SWHGoogleHugeArchiveCheckerTask(SWHGoogleArchiveCheckerTask):
    task_queue = 'swh_fetcher_googlecode_check_huge_archive'
