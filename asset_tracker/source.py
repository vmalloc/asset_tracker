import hashlib
import os
import pushy
import re
import logging

_logger = logging.getLogger(__name__)

class Source(object):
    def get_listing(self, ignored_patterns):
        raise NotImplementedError() # pragma: no cover
    def get_hashes_and_timestamps(self, filenames):
        raise NotImplementedError() # pragma: no cover
    def get_hostname(self):
        raise NotImplementedError() # pragma: no cover

class LocalSource(Source):
    def __init__(self, path):
        super(LocalSource, self).__init__()
        self._path = os.path.expanduser(path)
        _logger.debug("After expanduser: %s", self._path)
    def get_listing(self, ignored_patterns):
        ignored_patterns = [re.compile(p) for p in ignored_patterns]
        for path, _, filenames in os.walk(self._path):
            for filename in filenames:
                if any(p.match(filename) for p in ignored_patterns):
                    _logger.debug("Ignoring %s", filename)
                    continue
                filename = normalize_filename(os.path.join(path, filename))
                _logger.debug("Checking %s", filename)
                yield filename, get_timestamp(filename)
    def get_hashes_and_timestamps(self, filenames):
        return [(filename, get_full_hash(filename), get_timestamp(filename)) for filename in filenames]
    def __repr__(self):
        return "<localhost>"
    def get_hostname(self):
        return None

class RemoteSource(Source):
    def __init__(self, hostname, path, pushy_call=None):
        super(RemoteSource, self).__init__()
        self._hostname = hostname
        self._pushy_call = pushy_call
        self._path = path
    def _get_connection(self):
        hostname = "ssh:{}".format(self.get_hostname())
        if self._pushy_call is None:
            return pushy.connect(hostname)
        return self._pushy_call.apply(pushy.connect, hostname)
    def _get_remote_source(self):
        conn = self._get_connection()
        temp_dir = conn.modules.tempfile.mkdtemp()
        local_module_filename = __file__
        if local_module_filename.endswith(".pyc"):
            local_module_filename = local_module_filename[:-1]
        conn.putfile(local_module_filename, os.path.join(temp_dir, "assettracker__remote_module.py"))
        conn.modules.sys.path.insert(0, temp_dir)
        module = conn.modules.__builtin__.__import__("assettracker__remote_module")
        return  module.LocalSource(self._path)
    def get_listing(self, ignored_patterns):
        return self._get_remote_source().get_listing(ignored_patterns)
    def get_hashes_and_timestamps(self, filenames):
        return self._get_remote_source().get_hashes_and_timestamps(filenames)
    def __repr__(self):
        return "<ssh:{}>".format(self.get_hostname())
    def get_hostname(self):
        return self._hostname

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
