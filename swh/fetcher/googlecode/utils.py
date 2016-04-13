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


prefix_source_url_api = 'https://www.googleapis.com/storage/v1/b/google-code-archive-source/o'  # noqa
prefix_project_meta = 'https://storage.googleapis.com/google-code-archive'


def transform(url_gs):
    """Transform input gs:// url into a dictionary with the following
       information.

    Returns:
        Dict of the following form:
        - destination folder
        - filename
        - metadata archive url to fetch
        - project metadata url to fetch

    """
    url_gs = url_gs.replace('gs://google-code-archive-source/', '')
    filename = os.path.basename(url_gs)
    project_name = os.path.dirname(url_gs)
    url_meta = '%s/%s' % (prefix_source_url_api, url_gs.replace('/', '%2F'))
    url_project_meta = '%s/%s/project.json' % (prefix_project_meta,
                                               project_name)
    return {
        'parent_dir': compute_destination_folder(url_gs),
        'filename': filename,
        'url_project_archive_meta': url_meta,
        'url_project_meta': url_project_meta
    }
