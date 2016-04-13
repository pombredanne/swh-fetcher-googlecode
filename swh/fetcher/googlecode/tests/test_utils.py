# Copyright (C) 2016  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest

from nose.tools import istest

from swh.fetcher.googlecode.utils import transform


class TestUtils(unittest.TestCase):
    @istest
    def transform(self):
        input = 'gs://google-code-archive-source/v2/apache-extras.org/abhishsinha-cassandra-jdbc-source/source-archive.zip'  # noqa

        actual_gs_transformed = transform(input)

        self.assertEquals(
            actual_gs_transformed, {
                'parent_dir':
                'v2/apache-extras.org/a/abhishsinha-cassandra-jdbc-source',

                'filename':
                'source-archive.zip',

                'url_project_archive_meta':
                'https://www.googleapis.com/storage/v1/b/google-code-archive-source/o/v2%2Fapache-extras.org%2Fabhishsinha-cassandra-jdbc-source%2Fsource-archive.zip',  # noqa

                'url_project_meta':
                'https://storage.googleapis.com/google-code-archive/v2/apache-extras.org/abhishsinha-cassandra-jdbc-source/project.json'  # noqa
            })
