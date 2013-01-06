from asset_tracker import AssetTracker
from tempfile import mkdtemp
from unittest import TestCase
import os
import random

class AssetTrackerTest(TestCase):
    def setUp(self):
        super(AssetTrackerTest, self).setUp()
        self.root = mkdtemp()
        self.files = [os.path.join(self.root, "file.{}".format(extension)) for extension in ("jpg", "mov", "3gp", "avi", "png", "nef")]
        for filename in self.files:
            with open(filename, "wb") as outfile:
                outfile.write("some content of ")
                outfile.write(filename)
        self.tracker = AssetTracker()
        self.tracker.add_path(self.root)
        self.tracker.scan()
    def _change_file(self):
        filename = random.choice(self.files)
        with open(filename, "rb") as f:
            original_data = f.read()
        with open(filename, "ab") as f:
            f.write("X")
        return filename, original_data
