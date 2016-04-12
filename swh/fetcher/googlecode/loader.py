# Copyright (C) 2015-2016  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import logging
import os
import requests

from swh.core import config, hashutil

from .utils import transform
from .hashutil import crc32c_hash, md5_hash, md5_from_b64, crc32c_from_b64


# sample meta:
# {
#  "kind": "storage#object",                                                                                                                                                            # noqa
#  "id": "google-code-archive-source/v2/code.google.com/hg4j/source-archive.zip/1455746620701000",                                                                                      # noqa
#  "selfLink": "https://www.googleapis.com/storage/v1/b/google-code-archive-source/o/v2%2Fcode.google.com%2Fhg4j%2Fsource-archive.zip",                                                 # noqa
#  "name": "v2/code.google.com/hg4j/source-archive.zip",                                                                                                                                # noqa
#  "bucket": "google-code-archive-source",                                                                                                                                              # noqa
#  "generation": "1455746620701000",                                                                                                                                                    # noqa
#  "metageneration": "1",                                                                                                                                                               # noqa
#  "contentType": "application/octet-stream",                                                                                                                                           # noqa
#  "timeCreated": "2016-02-17T22:03:40.698Z",                                                                                                                                           # noqa
#  "updated": "2016-02-17T22:03:40.698Z",                                                                                                                                               # noqa
#  "storageClass": "NEARLINE",                                                                                                                                                          # noqa
#  "size": "4655405",                                                                                                                                                                   # noqa
#  "md5Hash": "FaIRjuSDe4v51H1+sRuggQ==",                                                                                                                                               # noqa
#  "mediaLink": "https://www.googleapis.com/download/storage/v1/b/google-code-archive-source/o/v2%2Fcode.google.com%2Fhg4j%2Fsource-archive.zip?generation=1455746620701000&alt=media", # noqa
#  "crc32c": "PNKIqA==",                                                                                                                                                                # noqa
#  "etag": "CMjy1uHm/8oCEAE="                                                                                                                                                           # noqa
# }


class SWHGoogleFetcher(config.SWHConfig):
    """A swh data fetcher loader.

    This fetcher will:

    - retrieve the archive metadata and write it to disk.

    - download the archive to retrieve and write it to disk.

    - check that size and checksums (md5, crc32c) match those describe
      in the metadata.

    """
    def __init__(self):
        self.log = logging.getLogger('swh.fetcher.google.SWHGoogleFetcher')

        l = logging.getLogger('requests.packages.urllib3.connectionpool')
        l.setLevel(logging.WARN)

    def retrieve_source_meta(self, url_meta, filepath_meta):
        if os.path.exists(filepath_meta):
            import json
            with open(filepath_meta, 'r') as f:
                meta = json.loads(f.read())
        else:
            meta = {}
            try:
                r = requests.get(url_meta)
            except Exception as e:
                msg = 'Problem when fetching metadata %s.' % url_meta
                self.log.error(msg)
                raise ValueError(msg, e)
            else:
                meta = r.json()

                with open(filepath_meta, 'w') as f:
                    f.write(r.text)

        return meta

    def retrieve_source(self, url, filepath):
        if not os.path.exists(filepath):
            self.log.debug('Fetching %s\' raw data.' % url)
            try:
                r = requests.get(url, stream=True)
            except Exception as e:
                msg = 'Problem when fetching file %s.' % url
                self.log.error(msg)
                raise ValueError(msg, e)
            else:
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(hashutil.HASH_BLOCK_SIZE):
                        f.write(chunk)

    def check_source(self, meta, filepath):
        expected = {
            'crc32c': crc32c_from_b64(meta['crc32c']),
            'md5': md5_from_b64(meta['md5Hash']),
            'size': int(meta['size'])
        }

        actual_size = os.path.getsize(filepath)
        if actual_size != expected['size']:
            msg = 'Bad size. Expected: %s. Got: %s' % (
                expected['size'], actual_size)
            self.log.error(msg)
            raise ValueError(msg)

        self.log.debug('Checking %s\' raw data checksums and size.' %
                       filepath)
        # Last, check the metadata are ok
        with open(filepath, 'rb') as f:
            md5_h = md5_hash(f)
            if md5_h != expected['md5']:
                msg = 'Bad md5 signature. Expected: %s. Got: %s' % (
                    expected['md5'], md5_h)
                self.log.error(msg)
                raise ValueError(msg)

            f.seek(0)

            crc32c_h = crc32c_hash(f)
            if expected['crc32c'] != crc32c_h:
                msg = 'Bad crc32c signature. Expected: %s. Got: %s' % (
                    expected['crc32c'], crc32c_h)
                self.log.error(msg)
                raise ValueError(msg)

    def process(self, archive_gs, destination_rootpath):
        self.log.info('Fetch %s\'s metadata' % archive_gs)

        # First retrieve the archive gs's metadata
        parent_dir, filename, url_meta, url_content = transform(
            archive_gs)

        parent_dir = os.path.join(destination_rootpath, parent_dir)

        os.makedirs(parent_dir, exist_ok=True)

        project_name = os.path.basename(parent_dir)

        filename = project_name + '-' + filename
        filename_meta = filename + '.json'

        filepath = os.path.join(parent_dir, filename)
        filepath_meta = os.path.join(parent_dir, filename_meta)

        meta = self.retrieve_source_meta(url_meta, filepath_meta)
        if not meta:
            raise ValueError('Fail to download metadata, stop.')

        # Second retrieve the actual content
        self.retrieve_source(meta['mediaLink'], filepath)

        # Third - Check the retrieved source
        try:
            self.check_source(meta, filepath)
        except ValueError as e:
            if os.path.exists(filepath):
                self.log.error('Clean corrupted file %s' % filepath)
                os.remove(filepath)
            raise e
        else:
            self.log.info('Archive %s fetched.' % archive_gs)
