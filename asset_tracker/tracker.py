from .alert import (
    ChangeAlert,
    DeletionAlert
)
from .asset import File
from .host import (
    LocalHost,
    RemoteHost,
)
from futures import ThreadPoolExecutor
import heapq
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
        self._dirs = {} # hostname -> paths
        self._hosts = {None : LocalHost()}

    def add_host(self, alias, hostname, **pushy_kwargs):
        self._hosts[alias] = RemoteHost(hostname, **pushy_kwargs)

    def iter_assets(self):
        return (asset for hostname, assets in self._state.assets.iteritems()
                for asset in assets.itervalues())

    def load_configuration(self, path):
        with open(os.path.expanduser(path)) as f:
            exec(f.read(), {"tracker" : self})

    def try_load_state(self, path):
        path = os.path.expanduser(path)
        try:
            with open(path, "rb") as f:
                state = pickle.load(f)
                assert not any(asset.get_saved_timestamp() is None
                               for host_assets in state.assets.itervalues()
                               for asset in host_assets.itervalues())
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

    def add_directory(self, path, hostname=None):
        self._dirs.setdefault(hostname, []).append(path)

    def get_alerts(self):
        return list(self._state.alerts)

    def clear_alert(self, alert):
        self._state.alerts.remove(alert)

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

    def get_identical_assets(self, asset):
        asset_hash = asset.get_hash()
        return [other for other in self.iter_assets() if other.get_hash() == asset_hash]

    def get_num_machines(self):
        return len(self._state.assets)

    def scan(self, scrub_count=0):
        now = datetime.datetime.now()
        for hostname in self._dirs:
            self._state.assets.setdefault(hostname, {})
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self._scan_single_host, hostname, host_dirs, now, scrub_count) for hostname, host_dirs in self._dirs.iteritems()]
            for future in futures:
                self._state.alerts.extend(future.result())
        num_new_files = 0
        for hostname, assets in self._state.assets.iteritems():
            for asset in assets.itervalues():
                if asset.get_first_seen() == now:
                    num_new_files += 1
        _logger.info("Scan finished. %s new files.", num_new_files)

    def _scan_single_host(self, hostname, paths, now, scrub_count):
        _logger.debug("Scanning %s", hostname)
        returned_alerts = []
        host = self._hosts[hostname]
        host_assets = self._state.assets.setdefault(hostname, {})
        need_hash = set()
        for path in paths:
            for filename, timestamp in host.get_listing(path, self._state.ignored_patterns):
                asset = host_assets.get(filename)
                if asset is None or asset.get_saved_timestamp() != timestamp:
                    _logger.debug("Going to need hash for %s (saved=%s, got=%s)",
                                  filename,
                                  asset.get_saved_timestamp() if asset else "none", timestamp)
                    need_hash.add(filename)
                else:
                    asset.notify_seen(now)
        _logger.debug("Getting scrub list (count=%s)...", scrub_count)
        for scrub_filename in self._get_scrub_list(host_assets, scrub_count):
            _logger.debug("Going to scrub %s", scrub_filename)
            need_hash.add(scrub_filename)
        if need_hash:
            for filename, file_hash, file_timestamp in host.get_hashes_and_timestamps(need_hash):
                asset = host_assets.get(filename)
                if asset is None:
                    _logger.debug("%s just created", filename)
                    asset = host_assets[filename] = File(now, hostname, filename, file_hash, file_timestamp)
                    assert asset.get_saved_timestamp() is not None
                elif asset.get_hash() != file_hash:
                    _logger.debug("%s changed hash!", filename)
                    returned_alerts.append(ChangeAlert(asset, asset.get_hash(), file_hash))
                asset.set_hash(now, file_hash)
                asset.notify_seen(now)
        returned_alerts.extend(self._remove_not_seen_now(hostname, now))
        return returned_alerts
    def _get_scrub_list(self, assets, count):
        returned = [
            filename
            for _, filename in heapq.nsmallest(count,
                    ((asset.get_last_hash_time(), filename)
                    for filename, asset in assets.iteritems()),
            )
        ]
        assert returned or count == 0 or not assets, "get_scrub_list returned empty"
        return returned
    def _remove_not_seen_now(self, hostname, now):
        returned_alerts = []
        not_seen = []
        for filename, cached_asset in self._state.assets[hostname].iteritems():
            if cached_asset.get_last_seen() != now:
                _logger.debug("%s is going to be removed", filename)
                not_seen.append(filename)
        for not_seen_filename in not_seen:
            returned_alerts.append(DeletionAlert(self._state.assets[hostname].pop(not_seen_filename)))
        return returned_alerts

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
