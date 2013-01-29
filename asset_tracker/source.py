import hashlib
import os

class Source(object):
    def get_listing(self, ignored_patterns):
        raise NotImplementedError() # pragma: no cover
    def get_hashes(self, filenames):
        raise NotImplementedError() # pragma: no cover

class LocalSource(Source):
    def __init__(self, path):
        super(LocalSource, self).__init__()
        self._path = path
    def get_listing(self, ignored_patterns):
        for path, _, filenames in os.walk(self._path):
            for filename in filenames:
                if any(p.match(filename) for p in ignored_patterns):
                    continue
                filename = normalize_filename(os.path.join(path, filename))
                yield filename, get_timestamp(filename)
    def get_hashes(self, filenames):
        return [(filename, get_full_hash(filename)) for filename in filenames]

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

def get_timestamp(filename):
    s = os.stat(filename)
    return s.st_mtime

def normalize_filename(f):
    return os.path.abspath(os.path.expanduser(os.path.normpath(os.path.realpath(f))))
