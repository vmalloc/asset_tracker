import pickle
from .asset import File
from .source import LocalSource
from .source import RemoteSource
from futures import ThreadPoolExecutor
import datetime
import fnmatch
import logging
import os

_logger = logging.getLogger(__name__)

class AssetTracker(object):
    def __init__(self):
        super(AssetTracker, self).__init__()
        self._state = AssetTrackerState()
        self._sources = []

    def load_configuration(self, path):
        with open(os.path.expanduser(path)) as f:
            exec(f.read(), {"tracker" : self, "LocalSource" : LocalSource, "RemoteSource" : RemoteSource})

    def try_load_state(self, path):
        path = os.path.expanduser(path)
        try:
            with open(path, "rb") as f:
                state = pickle.load(f)
                assert not any(asset.get_saved_timestamp() is None
                               for source_assets in state.assets.itervalues()
                               for asset in source_assets.itervalues())
        except IOError:
            pass
        else:
            self._state = state

    def save_state(self, path):
        path = os.path.expanduser(path)
        temp = path + ".tmp"
        with open(temp, "wb") as f:
            pickle.dump(self._state, f)
        os.rename(temp, path)

    def add_source(self, source):
        self._sources.append(source)

    def get_deleted_files(self):
        return list(self._state.deleted)

    def get_changed_files(self):
        return list(self._state.changed)

    def get_num_assets(self):
        return sum(len(x) for x in self._state.assets.itervalues())

    def get_num_machines(self):
        return len(self._state.assets)

    def scan(self):
        now = datetime.datetime.now()
        for source in self._sources:
            self._state.assets.setdefault(source.get_hostname(), {})
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self._scan_single_source, source, now) for source in self._sources]
            for future in futures:
                _ = future.result()
    def _scan_single_source(self, source, now):
        _logger.debug("Scanning %s", source)
        source_assets = self._state.assets.setdefault(source.get_hostname(), {})
        need_hash = []
        for filename, timestamp in source.get_listing(self._state.ignored_patterns):
            asset = source_assets.get(filename)
            if asset is None or asset.get_saved_timestamp() != timestamp:
                _logger.debug("Going to need hash for %s (saved=%s, got=%s)",
                              filename,
                              asset.get_saved_timestamp() if asset else "none", timestamp)
                need_hash.append(filename)
            else:
                asset.notify_seen(now)
        if need_hash:
            for filename, file_hash, file_timestamp in source.get_hashes_and_timestamps(need_hash):
                asset = source_assets.get(filename)
                if asset is None:
                    _logger.debug("%s just created", filename)
                    asset = source_assets[filename] = File(source, filename, file_hash, file_timestamp)
                    assert asset.get_saved_timestamp() is not None
                elif asset.get_hash() != file_hash:
                    _logger.debug("%s changed hash!", filename)
                    self._state.changed.append((asset, asset.get_hash(), file_hash))
                    asset.set_hash(file_hash)
                asset.notify_seen(now)
        self._remove_not_seen_now(source, now)
    def _remove_not_seen_now(self, source, now):
        not_seen = []
        for filename, cached_asset in self._state.assets[source.get_hostname()].iteritems():
            if cached_asset.get_last_seen() != now:
                _logger.debug("%s is going to be removed", filename)
                not_seen.append(filename)
        for not_seen_filename in not_seen:
            self._state.deleted.append(self._state.assets[source.get_hostname()].pop(not_seen_filename))

class AssetTrackerState(object):
    def __init__(self):
        super(AssetTrackerState, self).__init__()
        self.ignored_patterns = [
            fnmatch.translate(f)
            for f in [
                    ".DS_Store",
            ]
        ]
        self.assets = {}
        self.deleted = []
        self.changed = []
