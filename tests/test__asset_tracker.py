from .test_utils import AssetTrackerTest
from asset_tracker.host import normalize_filename
import os

class TrackerTest(AssetTrackerTest):
    def test__nothing_changes(self):
        self.tracker.scan()
        self.assertEquals(self.tracker.get_deleted_files(), [])
    def test__hash_changes_local(self):
        self._test__hash_changes(remote=False)
    def test__hash_changes_remote(self):
        self._test__hash_changes(remote=True)
    def _test__hash_changes(self, remote):
        filename, _ = self._change_file(remote=remote)
        self.tracker.scan()
        [deleted] = self.tracker.get_changed_files()
        self.assertEquals(os.path.basename(deleted.get_filename()), os.path.basename(filename))
    def test__mtime_changes_local(self):
        self._test__mtime_changes(remote=True)
    def test__mtime_changes_remote(self):
        self._test__mtime_changes(remote=False)
    def _test__mtime_changes(self, remote):
        hostname, conn = self._get_hostname_conn(remote=remote)
        filename, original_contents = self._change_file(remote=remote)
        with conn.modules.__builtin__.open(filename, "wb") as f:
            f.write(original_contents)
        self.tracker.scan()
        self.assertNoAlerts()
    def test__ignored_files_remote(self):
        self._test__ignored_files(remote=True)
    def test__ignored_files_local(self):
        self._test__ignored_files(remote=False)
    def test__load_save_state(self):
        "Test saving and loading state file, including data migration"
        tempfile = "/tmp/__temp_state"
        self.tracker.scan()
        self.tracker._state.changed = []
        self.tracker._state.deleted = []
        del self.tracker._state.alerts
        self.tracker.save_state(tempfile)
        self.tracker._state = None
        self.tracker.try_load_state(tempfile)
        self.assertIsNotNone(self.tracker._state)
        self.assertTrue(hasattr(self.tracker._state, "alerts"))
        self.assertFalse(hasattr(self.tracker._state, "changed"))
        self.assertFalse(hasattr(self.tracker._state, "deleted"))
    def _test__ignored_files(self, remote):
        hostname, conn = self._get_hostname_conn(remote=remote)
        ignored_file = os.path.join(self.roots[hostname], ".DS_Store")
        with conn.modules.__builtin__.open(ignored_file, "w") as f:
            f.write("ds store")
        self.tracker.scan()
        self.assertNoAlerts()
        conn.modules.os.unlink(ignored_file)
        self.tracker.scan()
        self.assertNoAlerts()
    def _get_hostname_conn(self, remote):
        hostname = "vagrant" if remote else "localhost"
        return hostname, self.conns[hostname]
    def assertNoAlerts(self):
        self.assertEquals(self.tracker.get_alerts(), [])
        self.assertEquals(self.tracker.get_deleted_files(), [])
        self.assertEquals(self.tracker.get_changed_files(), [])
