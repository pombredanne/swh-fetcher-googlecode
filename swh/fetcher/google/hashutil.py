# Copyright (C) 2015-2016  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import crcmod.predefined
import hashlib
import sys
import base64

from swh.model import hashutil


# crc32_func = crcmod.mkCrcFun(0x104c11db7, initCrc=0x00000000, xorOut=0xffffffff)
# crc32c_func = crcmod.mkCrcFun(0x11edc6f41, initCrc=0x00000000, xorOut=0xffffffff)
crc32c_func = crcmod.predefined.mkCrcFun('crc-32c')


def crc32c_hash(fobj):
    h = 0
    while True:
        chunk = fobj.read(hashutil.HASH_BLOCK_SIZE)
        if not chunk:
            break
        h = crc32c_func(chunk, h)

    # convert checksum to hex bytes
    return h.to_bytes((h.bit_length() // 8) + 1, byteorder='big')



def md5(fobj):
    h = hashlib.md5()
    while True:
        chunk = fobj.read(hashutil.HASH_BLOCK_SIZE)
        if not chunk:
            break
        h.update(chunk)

    return h.digest()


if __name__ == '__main__':
    # filename = sys.argv[1]
    filename = 'hg4j.zip'
    # meta: https://www.googleapis.com/storage/v1/b/google-code-archive-source/o/v2%2Fcode.google.com%2Fhg4j%2Fsource-archive.zip
    # file: https://www.googleapis.com/storage/v1/b/google-code-archive-source/o/v2%2Fcode.google.com%2Fhg4j%2Fsource-archive.zip?alt=media

    expected_md5 = base64.b64decode(b'FaIRjuSDe4v51H1+sRuggQ==')
    expected_crc32c = base64.decodebytes(b'PNKIqA==')

    with open(filename, 'rb') as f:
        md5_hash = md5(f)
        if md5_hash != expected_md5:
            print('Expected md5: %s - Computed md5: %s' % (
                expected_md5, md5_hash))

        f.seek(0)

        crc32c_hash_signed = crc32c_hash(f)
        if crc32c_hash_signed != expected_crc32c:
            print('expected_crc32c: %s - Computed crc32c: %s' % (
                expected_crc32c, crc32c_hash_signed))
