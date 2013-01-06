from .alert import Alert
from .asset import Asset, CachedAsset
from .utils import get_full_hash
from .utils import normalize_filename
import datetime
import fnmatch
import logging
import os
import re

_logger = logging.getLogger(__name__)

class AssetTracker(object):
    def __init__(self):
        super(AssetTracker, self).__init__()
        self._state = AssetTrackerState()

    def add_path(self, path):
        self._state.paths.append(path)

    def scan(self):
        now = datetime.datetime.now()
        for filename in self._iter_filenames():
            _logger.debug("Scanning %s...", filename)
            self._scan_single_file(filename, now)
        removed_hashes = set()
        for asset in self._state.assets.itervalues():
            seen_filenames = [f for f, when in asset.get_filenames().iteritems() if when == now]
            if not seen_filenames:
                self._state.alerts.append(Alert(asset, "Asset disappeared"))
                removed_hashes.add(asset.get_hash())
        for removed_hash in removed_hashes:
            self._remove_asset_by_hash(removed_hash)

    def _scan_single_file(self, filename, now):
        cached_asset = self._state.asset_cache.get(filename)
        if cached_asset is not None and not cached_asset.has_changed():
            _logger.debug("%s has not changed", filename)
            asset = self._state.assets[cached_asset.get_hash()]
        else:
            _logger.debug("%s has changed or did not exist", filename)
            asset = Asset(get_full_hash(filename))
            cached_asset = CachedAsset(filename, asset.get_hash())
            self._state.assets[asset.get_hash()] = asset
            self._state.asset_cache[filename] = cached_asset
        asset.notify_seen(filename, now)

    def _remove_asset_by_hash(self, h):
        asset = self._state.assets.pop(h)
        for filename in asset.get_filenames():
            self._state.asset_cache.pop(filename, None)

    def _iter_filenames(self):
        for p in self._state.paths:
            for path, _, filenames in os.walk(p):
                for filename in filenames:
                    if any(p.match(filename) for p in self._state.ignored_patterns):
                        continue
                    yield normalize_filename(os.path.join(path, filename))
    def get_alerts(self):
        return list(self._state.alerts)

class AssetTrackerState(object):
    def __init__(self):
        super(AssetTrackerState, self).__init__()
        self.ignored_patterns = [
            re.compile(fnmatch.translate(f))
            for f in [
                    ".DS_Store",
            ]
        ]

        self.asset_cache = {}
        self.assets = {}
        self.paths = []
        self.alerts = []
