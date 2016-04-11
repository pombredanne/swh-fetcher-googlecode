# Copyright (C) 2015-2016  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import click
import sys

task_name = 'swh.fetcher.google.tasks.SWHGoogleFetcherTask'


@click.command()
@click.option('--gs-url',
              help="gs repository's remote url.")
@click.option('--destination-rootpath',
              help="Root destination to write the data.")
def produce(gs_url, destination_rootpath='/srv/storage/space/mirrors/code.google.com/sources/'):
    from swh.scheduler.celery_backend.config import app
    from swh.fetcher.google import tasks  # noqa

    print('%s sent for download and checks.' % gs_url)

    task = app.tasks[task_name]
    if gs_url:  # for debug purpose
        task.delay(gs_url, destination_rootpath)
    else:  # synchroneous flag is ignored in that case
        for gs_url in sys.stdin:
            gs_url = gs_url.rstrip()
            print(gs_url)
            task.delay(gs_url, destination_rootpath)


if __name__ == '__main__':
    produce()
