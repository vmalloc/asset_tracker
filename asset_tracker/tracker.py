from .alert import (
    ChangeAlert,
    DeletionAlert
)
from .asset import File
from .source import LocalSource
from .source import RemoteSource
from futures import ThreadPoolExecutor
import copy
import datetime
import fnmatch
import logging
import os
import pickle

_logger = logging.getLogger(__name__)

class AssetTracker(object):
    def __init__(self):
        super(AssetTracker, self).__init__()
        self._state = AssetTrackerState()
        self._sources = []

    def iter_assets(self):
        return (copy.deepcopy(asset) for hostname, assets in self._state.assets.iteritems()
                for asset in assets.itervalues())

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
            for obsolete_attr in ["changed", "deleted"]:
                if hasattr(state, obsolete_attr):
                    assert not getattr(state, obsolete_attr)
                    delattr(state, obsolete_attr)
            for possibly_missing, default in [
                    ("alerts", []),
                    ]:
                if not hasattr(state, possibly_missing):
                    setattr(state, possibly_missing, default)
            self._state = state

    def save_state(self, path):
        path = os.path.expanduser(path)
        temp = path + ".tmp"
        with open(temp, "wb") as f:
            pickle.dump(self._state, f)
        os.rename(temp, path)

    def add_source(self, source):
        self._sources.append(source)

    def get_alerts(self):
        return list(self._state.alerts)

    def get_deleted_files(self):
        return self._get_alert_files(DeletionAlert)

    def get_changed_files(self):
        return self._get_alert_files(ChangeAlert)

    def _get_alert_files(self, alert_class):
        return [alert.asset for alert in self._get_alerts(alert_class)]

    def _get_alerts(self, alert_class):
        return [alert for alert in self._state.alerts if isinstance(alert, alert_class)]

    def get_num_assets(self):
        return sum(len(x) for x in self._state.assets.itervalues())

    def get_num_machines(self):
        return len(self._state.assets)

    def scan(self):
        now = datetime.datetime.now()
        for source in self._sources:
            self._state.assets.setdefault(source.get_hostname(), {})
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self._scan_single_host, hostname, sources, now) for hostname, sources in self._group_sources_by_hostname()]
            for future in futures:
                _ = future.result()

    def _group_sources_by_hostname(self):
        sources_by_hostname = {}
        for source in self._sources:
            sources_by_hostname.setdefault(source.get_hostname(), []).append(source)
        return sources_by_hostname.iteritems()

    def _scan_single_host(self, hostname, sources, now):
        _logger.debug("Scanning %s", hostname)
        host_assets = self._state.assets.setdefault(hostname, {})
        need_hash = {}
        for source in sources:
            for filename, timestamp in source.get_listing(self._state.ignored_patterns):
                asset = host_assets.get(filename)
                if asset is None or asset.get_saved_timestamp() != timestamp:
                    _logger.debug("Going to need hash for %s (saved=%s, got=%s)",
                                  filename,
                                  asset.get_saved_timestamp() if asset else "none", timestamp)
                    need_hash.setdefault(source, []).append(filename)
                else:
                    asset.notify_seen(now)
        if need_hash:
            for source, filenames in need_hash.iteritems():
                for filename, file_hash, file_timestamp in source.get_hashes_and_timestamps(filenames):
                    asset = host_assets.get(filename)
                    if asset is None:
                        _logger.debug("%s just created", filename)
                        asset = host_assets[filename] = File(hostname, filename, file_hash, file_timestamp)
                        assert asset.get_saved_timestamp() is not None
                    elif asset.get_hash() != file_hash:
                        _logger.debug("%s changed hash!", filename)
                        self._state.alerts.append(ChangeAlert(asset, asset.get_hash(), file_hash))
                        asset.set_hash(file_hash)
                    asset.notify_seen(now)
        self._remove_not_seen_now(hostname, now)
    def _remove_not_seen_now(self, hostname, now):
        not_seen = []
        for filename, cached_asset in self._state.assets[hostname].iteritems():
            if cached_asset.get_last_seen() != now:
                _logger.debug("%s is going to be removed", filename)
                not_seen.append(filename)
        for not_seen_filename in not_seen:
            self._state.alerts.append(DeletionAlert(self._state.assets[hostname].pop(not_seen_filename)))

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
        self.alerts = []
