# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.scheduler.task import Task
from .fetcher import SWHGoogleArchiveFetcher


class SWHGoogleArchiveFetcherTask(Task):
    """Main task to fetch files from google code archive server.

    """
    task_queue = 'swh_fetcher_googlecode_fetch_archive'

    def run(self, archive_gs, destination_rootpath):
        SWHGoogleArchiveFetcher().process(archive_gs, destination_rootpath)
