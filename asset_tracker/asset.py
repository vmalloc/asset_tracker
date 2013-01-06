import os

class Asset(object):
    def __init__(self, hash):
        super(Asset, self).__init__()
        self._hash = hash
        self._filenames = {}
    def notify_seen(self, filename, when):
        self._filenames[filename] = when
    def get_hash(self):
        return self._hash
    def get_filenames(self):
        return self._filenames.copy()

class CachedAsset(object):
    def __init__(self, filename, hash):
        super(CachedAsset, self).__init__()
        self._filename = filename
        stat = os.stat(filename)
        self._sig = self._get_signature()
        self._hash = hash
    def get_hash(self):
        return self._hash
    def has_changed(self):
        return self._get_signature() != self._sig
    def _get_signature(self):
        stat = os.stat(self._filename)
        return (stat.st_mtime, stat.st_size)
