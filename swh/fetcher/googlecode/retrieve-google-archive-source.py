# Copyright (C) 2015-2016  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


import sys
import os
import requests

from . import utils


if __name__ == '__main__':
    for archive in sys.stdin:
        archive_gs = archive.rstrip()
        data = utils.transform(  # noqa
            archive_gs)

        parent_dir = data['parent_dir']
        filename = data['filename']
        url_project_archive_meta = data['url_project_archive_meta']
        url_project_meta = data['url_project_meta']
        os.makedirs(parent_dir, exist_ok=True)

        project_name = os.path.basename(parent_dir)
        filename = project_name + '-' + filename + '.json'

        try:
            r = requests.get(url_project_archive_meta)
        except:
            archive_size = ''
        else:
            archive_size = r.json()['size']

        repo_type = ''
        try:
            r = requests.get(url_project_meta)
        except:
            repo_type = ''
        else:
            repo_type = r.json()['repoType']

        print(filename, archive_size, repo_type)
