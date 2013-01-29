from .test_utils import AssetTrackerTest
from asset_tracker.source import normalize_filename
import os

class TrackerTest(AssetTrackerTest):
    def test__nothing_changes(self):
        self.tracker.scan()
        self.assertEquals(self.tracker.get_deleted_files(), [])
    def test__hash_changes(self):
        filename, _ = self._change_file()
        self.tracker.scan()
        [(deleted, old_hash, new_hash)] = self.tracker.get_changed_files()
        self.assertEquals(deleted.get_filename(), normalize_filename(filename))
    def test__mtime_changes(self):
        filename, original_contents = self._change_file()
        with open(filename, "wb") as f:
            f.write(original_contents)
        self.tracker.scan()
        self.assertNoAlerts()
    def test__ignored_files(self):
        ignored_file = os.path.join(self.root, ".DS_Store")
        with open(ignored_file, "w") as f:
            f.write("ds store")
        self.tracker.scan()
        self.assertNoAlerts()
        os.unlink(ignored_file)
        self.tracker.scan()
        self.assertNoAlerts()
    def assertNoAlerts(self):
        self.assertEquals(self.tracker.get_deleted_files(), [])
        self.assertEquals(self.tracker.get_changed_files(), [])
