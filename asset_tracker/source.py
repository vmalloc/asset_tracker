import hashlib
import os
import pushy
import re
import logging

_logger = logging.getLogger(__name__)

class Source(object):
    def get_listing(self, path, ignored_patterns):
        raise NotImplementedError() # pragma: no cover
    def get_hashes_and_timestamps(self, filenames):
        raise NotImplementedError() # pragma: no cover
    def get_hostname(self):
        raise NotImplementedError() # pragma: no cover

class LocalSource(Source):
    def get_listing(self, root_path, ignored_patterns):
        root_path = os.path.expanduser(root_path)
        _logger.debug("After expanduser: %s", root_path)
        ignored_patterns = [re.compile(p) for p in ignored_patterns]
        for path, _, filenames in os.walk(root_path):
            for filename in filenames:
                if any(p.match(filename) for p in ignored_patterns):
                    _logger.debug("Ignoring %s", filename)
                    continue
                orig_filename = os.path.join(path, filename)
                filename = normalize_filename(orig_filename)
                _logger.debug("Checking %s", filename)
                try:
                    yield filename, get_timestamp(filename)
                except OSError as e:
                    _logger.warning("Ignoring %s (%s)", orig_filename, e)
    def get_hashes_and_timestamps(self, filenames):
        returned = []
        for filename in filenames:
            try:
                returned.append((filename, get_full_hash(filename), get_timestamp(filename)))
            except OSError as e:
                _logger.warning("Ignoring %s (%s)", filename, e)
        return returned
    def __repr__(self):
        return "<localhost>"
    def get_hostname(self):
        return None

class RemoteSource(Source):
    def __init__(self, pushy_call):
        super(RemoteSource, self).__init__()
        self._pushy_call = pushy_call
    def _get_connection(self):
        return self._pushy_call.apply(pushy.connect)
    def _get_remote_source(self):
        conn = self._get_connection()
        temp_dir = conn.modules.tempfile.mkdtemp()
        local_module_filename = __file__
        if local_module_filename.endswith(".pyc"):
            local_module_filename = local_module_filename[:-1]
        conn.putfile(local_module_filename, os.path.join(temp_dir, "assettracker__remote_module.py"))
        conn.modules.sys.path.insert(0, temp_dir)
        module = conn.modules.__builtin__.__import__("assettracker__remote_module")
        return  module.LocalSource()
    def get_listing(self, root_path, ignored_patterns):
        return self._get_remote_source().get_listing(root_path, ignored_patterns)
    def get_hashes_and_timestamps(self, filenames):
        return self._get_remote_source().get_hashes_and_timestamps(filenames)

_BLOCK_SIZE = 4096

def get_full_hash(filename):
    h = hashlib.sha256()
    with open(filename, "rb") as f:
        while True:
            b = f.read(_BLOCK_SIZE)
            if not b:
                break
            h.update(b)
    return (os.path.getsize(filename), h.digest())

def get_timestamp(filename):
    s = os.stat(filename)
    return s.st_mtime

def normalize_filename(f):
    return os.path.abspath(os.path.expanduser(os.path.normpath(os.path.realpath(f))))
