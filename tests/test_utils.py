from asset_tracker import AssetTracker, LocalSource, RemoteSource
from unittest import TestCase
import os
import time
import random
import logging
from . import (
    get_pushy_connection,
    get_local_connection,
    )

_logger = logging.getLogger(__name__)

class AssetTrackerTest(TestCase):
    def setUp(self):
        super(AssetTrackerTest, self).setUp()
        self.files = {}
        self.roots = {}
        self.conns = {"vagrant" : get_pushy_connection(), "localhost" : get_local_connection()}
        for hostname, conn in self.conns.iteritems():
            root = self.roots[hostname] = conn.modules.tempfile.mkdtemp()
            self.files[hostname] = [conn.modules.os.path.join(root, "file.{}".format(extension))
                                    for extension in ("jpg", "mov", "3gp", "avi", "png", "nef")]
        mtime = time.time() - 100

        for hostname, files in self.files.iteritems():
            conn = self.conns[hostname]
            for filename in files:
                with conn.modules.__builtin__.open(filename, "wb") as outfile:
                    outfile.write("some content of ")
                    outfile.write(filename)
                conn.modules.os.utime(filename, (mtime, mtime))
        self.tracker = AssetTracker()
        self.tracker.add_source(LocalSource(self.roots["localhost"]))
        self.tracker.add_source(RemoteSource(get_pushy_connection(), self.roots["vagrant"]))
        self.tracker.scan()
    def _change_file(self, remote):
        hostname = "vagrant" if remote else "localhost"
        conn = self.conns[hostname]
        filename = random.choice(self.files[hostname])
        _logger.debug("Changing %s", filename)
        with conn.modules.__builtin__.open(filename, "rb") as f:
            original_data = f.read()
        with conn.modules.__builtin__.open(filename, "ab") as f:
            f.write("X")
        return filename, original_data
