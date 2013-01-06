import hashlib
import os

_BLOCK_SIZE = 4096

def get_full_hash(filename):
    h = hashlib.sha256()
    with open(filename, "rb") as f:
        while True:
            b = f.read(_BLOCK_SIZE)
            if not b:
                break
            h.update(b)
    return h.digest()

def normalize_filename(f):
    return os.path.abspath(os.path.expanduser(os.path.normpath(os.path.realpath(f))))
