# Copyright (C) 2015-2016  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import hashlib
import logging
import os
import requests

from swh.core import config, hashutil

from .utils import transform
from .hashutil import md5_hash, md5_from_b64


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

    def load_meta(self, filepath):
        """Try and load the metadata from the given filepath.
           It is assumed that the code is called after checking the file
           exists.

        """
        import json
        try:
            with open(filepath, 'r') as f:
                return json.loads(f.read())
        except:
            return None

    def retrieve_source_meta(self, url_meta, filepath_meta):
        if os.path.exists(filepath_meta):
            meta = self.load_meta(filepath_meta)
            if meta:  # some meta could be corrupted, so we try to load them
                return meta
            # and if we fail, we try to fetch them again

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

    def write_and_check(self, filepath, response, md5h):
        """Write the response's stream content to filepath.
           Compute the hash at the same time and ensure the md5h is the same.

           Returns:
               True if everything is ok and the md5 computed match the content.
               False otherwise
        """
        h = hashlib.md5()
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(hashutil.HASH_BLOCK_SIZE):
                f.write(chunk)
                h.update(chunk)

        return md5h == h.digest()

    def retrieve_source(self, archive_gs, meta, filepath):
        url = meta['mediaLink']
        if not os.path.exists(filepath):
            self.log.debug('Fetching %s\' raw data.' % url)
            try:
                r = requests.get(url, stream=True)
            except Exception as e:
                msg = 'Problem when fetching archive %s from url %s.' % (
                    archive_gs, url)
                self.log.error(msg)
                raise ValueError(msg, e)
            else:
                if not r.ok:
                    msg = 'Problem when fetching archive %s from url %s.' % (
                        archive_gs, url)
                    self.log.error(msg)
                    raise ValueError(msg)

                return self.write_and_check(filepath,
                                            r,
                                            md5_from_b64(meta['md5Hash']))

    def check_source_ok(self, meta, filepath, with_md5=False):
        expected_size = int(meta['size'])
        ok = True
        actual_size = os.path.getsize(filepath)
        if actual_size != expected_size:
            msg = 'Bad size. Expected: %s. Got: %s' % (
                expected_size, actual_size)
            self.log.error(msg)
            ok = False

        if with_md5:
            expected_md5 = md5_from_b64(meta['md5Hash'])
            self.log.debug('Checking %s\' raw data checksums and size.' %
                           filepath)
            # Last, check the metadata are ok
            with open(filepath, 'rb') as f:
                md5_h = md5_hash(f)
                if md5_h != expected_md5:
                    msg = 'Bad md5 signature. Expected: %s. Got: %s' % (
                        expected_md5, md5_h)
                    self.log.error(msg)
                    ok = False

        return ok

    def process(self, archive_gs, destination_rootpath):
        self.log.info('Fetch %s\'s metadata' % archive_gs)

        # First retrieve the archive gs's metadata
        data = transform(archive_gs)

        parent_dir = data['parent_dir']
        filename = data['filename']
        url_project_archive_meta = data['url_project_archive_meta']
        url_project_meta = data['url_project_meta']

        parent_dir = os.path.join(destination_rootpath, parent_dir)

        os.makedirs(parent_dir, exist_ok=True)

        project_name = os.path.basename(parent_dir)

        filename = project_name + '-' + filename
        filename_meta = filename + '.json'

        filepath = os.path.join(parent_dir, filename)
        filepath_meta = os.path.join(parent_dir, filename_meta)
        filepath_project_meta = os.path.join(parent_dir, 'project.json')

        meta = self.retrieve_source_meta(url_project_archive_meta,
                                         filepath_meta)
        if not meta:
            raise ValueError('Fail to download archive source metadata, stop.')

        project_meta = self.retrieve_source_meta(url_project_meta,
                                                 filepath_project_meta)
        if not project_meta:
            raise ValueError('Fail to download project metadata, stop.')

        # check existence of the file
        if os.path.exists(filepath):
            # it already exists, check it's ok
            checks_ok = self.check_source_ok(meta, filepath, with_md5=True)
            if checks_ok:  # it's ok, we are done
                self.log.info('Archive %s already fetched!' % archive_gs)
                return

            self.log.error('Clean corrupted file %s' % filepath)
            os.remove(filepath)

        # the file does not exist, we retrieve it
        checks_ok = self.retrieve_source(archive_gs, meta, filepath)

        # Third - Check the retrieved source
        if checks_ok and self.check_source_ok(meta, filepath):
            self.log.info('Archive %s fetched.' % archive_gs)
            return

        # Trouble, we rename the corrupted file
        if os.path.exists(filepath):
            filepath_corrupted = filepath + '.corrupted'
            self.log.error('Rename corrupted file %s to %s' % (
                os.path.basename(filepath),
                os.path.basename(filepath_corrupted)))
            os.rename(filepath, filepath_corrupted)
