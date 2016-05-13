# Copyright (C) 2015-2016  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import click
import sys


task_name = 'swh.fetcher.googlecode.tasks.SWHGoogleArchiveCheckerTask'


@click.command()
@click.option('--archive-path',
              help="Archive path to check")
@click.option('--temp-dir',
              help="Temporary folder to make check computations on archive.")
def produce(archive_path, temp_dir):
    from swh.scheduler.celery_backend.config import app
    from swh.fetcher.googlecode import tasks  # noqa

    task = app.tasks[task_name]
    if archive_path:  # for debug purpose, one archive
        task.delay(archive_path, temp_dir)
    else:  # otherwise, we deal in archive_path batch
        for archive_path in sys.stdin:
            archive_path = archive_path.rstrip()
            print(archive_path)
            task.delay(archive_path, temp_dir)


if __name__ == '__main__':
    produce()
