from asset_tracker import AssetTracker, LocalSource
from tempfile import mkdtemp
from unittest import TestCase
import os
import time
import random
import logging

_logger = logging.getLogger(__name__)

class AssetTrackerTest(TestCase):
    def setUp(self):
        super(AssetTrackerTest, self).setUp()
        self.root = mkdtemp()
        self.files = [os.path.join(self.root, "file.{}".format(extension)) for extension in ("jpg", "mov", "3gp", "avi", "png", "nef")]
        mtime = time.time() - 100
        for filename in self.files:
            with open(filename, "wb") as outfile:
                outfile.write("some content of ")
                outfile.write(filename)
            os.utime(filename, (mtime, mtime))
        self.tracker = AssetTracker()
        self.tracker.add_source(LocalSource(self.root))
        self.tracker.scan()
    def _change_file(self):
        filename = random.choice(self.files)
        _logger.debug("Changing %s", filename)
        with open(filename, "rb") as f:
            original_data = f.read()
        with open(filename, "ab") as f:
            f.write("X")
        return filename, original_data
