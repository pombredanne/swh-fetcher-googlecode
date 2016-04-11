# Copyright (C) 2015-2016  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


import os


def compute_destination_folder(path):
    """Given a path, compute a destination folder to which downloads the
       remote files.

    """
    parent_dir = os.path.dirname(path)
    project_name = os.path.basename(parent_dir)
    parent_ddir = os.path.dirname(parent_dir)
    return os.path.join(parent_ddir, project_name[0], project_name)


prefix_url_api = 'https://www.googleapis.com/storage/v1/b/google-code-archive-source/o'  # noqa


def transform(url_gs):
    """Transform input gs:// url into:
        - destination folder
        - filename
        - metadata url to fetch
        - actual content to fetch
    """
    url_gs = url_gs.replace('gs://google-code-archive-source/', '')
    filename = os.path.basename(url_gs)
    url_meta = '%s/%s' % (prefix_url_api, url_gs.replace('/', '%2F'))
    parent_dir = compute_destination_folder(url_gs)
    return parent_dir, filename, url_meta, '%s?alt=media' % url_meta
