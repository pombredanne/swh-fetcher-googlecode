# Copyright (C) 2015-2016  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


import sys
import os
import requests

from swh.fetcher.google import utils


if __name__ == '__main__':
    for archive in sys.stdin:
        archive_gs = archive.rstrip()
        parent_dir, filename, url_meta, url_content = utils.transform(
            archive_gs)
        os.makedirs(parent_dir, exist_ok=True)

        project_name = os.path.basename(parent_dir)
        filename = project_name + '-' + filename + '.json'

        try:
            r = requests.get(url_meta)
        except:
            print('', filename)
        else:
            print(r.json()['size'], filename)

            # we store the project metadata
            filepath = os.path.join(parent_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(r.text.encode('utf-8'))
