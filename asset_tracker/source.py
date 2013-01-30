import hashlib
import os
import re

class Source(object):
    def get_listing(self, ignored_patterns):
        raise NotImplementedError() # pragma: no cover
    def get_hashes_and_timestamps(self, filenames):
        raise NotImplementedError() # pragma: no cover

class LocalSource(Source):
    def __init__(self, path):
        super(LocalSource, self).__init__()
        self._path = path
    def get_listing(self, ignored_patterns):
        ignored_patterns = [re.compile(p) for p in ignored_patterns]
        for path, _, filenames in os.walk(self._path):
            for filename in filenames:
                if any(p.match(filename) for p in ignored_patterns):
                    continue
                filename = normalize_filename(os.path.join(path, filename))
                yield filename, get_timestamp(filename)
    def get_hashes_and_timestamps(self, filenames):
        return [(filename, get_full_hash(filename), get_timestamp(filename)) for filename in filenames]

class RemoteSource(Source):
    def __init__(self, pushy_connection, path):
        super(RemoteSource, self).__init__()
        self._conn = pushy_connection
        temp_dir = self._conn.modules.tempfile.mkdtemp()
        local_module_filename = __file__
        if local_module_filename.endswith(".pyc"):
            local_module_filename = local_module_filename[:-1]
        self._conn.putfile(local_module_filename, os.path.join(temp_dir, "assettracker__remote_module.py"))
        self._conn.modules.sys.path.insert(0, temp_dir)
        self._mod = self._conn.modules.__builtin__.__import__("assettracker__remote_module")
        self._conn.modules.sys.path.pop(0)
        self._source = self._mod.LocalSource(path)
    def get_listing(self, ignored_patterns):
        return self._source.get_listing(ignored_patterns)
    def get_hashes_and_timestamps(self, filenames):
        return self._source.get_hashes_and_timestamps(filenames)

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
