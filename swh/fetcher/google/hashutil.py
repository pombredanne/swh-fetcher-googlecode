# Copyright (C) 2015-2016  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import base64
import crcmod.predefined
import hashlib
import os
import struct

from swh.model import hashutil


crc32c_func = crcmod.predefined.mkCrcFun('crc-32c')


def crc32c_hash(fobj):
    h = 0
    while True:
        chunk = fobj.read(hashutil.HASH_BLOCK_SIZE)
        if not chunk:
            break
        h = crc32c_func(chunk, h)

    return h


def crc32c_from_b64(crc32c_b64):
    return struct.unpack('>L', base64.b64decode(crc32c_b64))[0]


def md5_from_b64(md5_b64):
    return base64.b64decode(md5_b64)


def md5_hash(fobj):
    h = hashlib.md5()
    while True:
        chunk = fobj.read(hashutil.HASH_BLOCK_SIZE)
        if not chunk:
            break
        h.update(chunk)

    return h.digest()


if __name__ == '__main__':
    import sys
    filename = sys.argv[1]
    filename_meta = filename + '.json'
    import json

    with open(filename_meta, 'r') as f:
        data = json.loads(f.read())

    expected_md5 = md5_from_b64(data['md5Hash'])
    expected_crc32c = crc32c_from_b64(data['crc32c'])

    with open(filename, 'rb') as f:
        md5_h = md5_hash(f)
        print('Expected md5: %s - Computed md5: %s' % (
            expected_md5, md5_h))
        if md5_h != expected_md5:
            print('md5 does not match')

        f.seek(0)

        crc32c_h = crc32c_hash(f)
        print('expected_crc32c: %s - Computed crc32c: %s' % (
            expected_crc32c, crc32c_h))
        if expected_crc32c != crc32c_h:
            print('crc32c does not match.')
