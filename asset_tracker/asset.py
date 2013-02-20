class File(object):
    def __init__(self, scan_time, hostname, filename, file_hash, file_timestamp):
        super(File, self).__init__()
        self._hostname = hostname
        self._filename = filename
        self.set_hash(scan_time, file_hash)
        self._hash = file_hash
        self._last_hash_time = scan_time
        self._first_seen = scan_time
        self._last_seen = None
        self._saved_timestamp = file_timestamp
    def get_filename(self):
        return self._filename
    def get_hash(self):
        return self._hash
    def set_hash(self, when, h):
        self._hash = h
        self._last_hash_time = when
    def notify_seen(self, when):
        self._last_seen = when
    def get_last_seen(self):
        return self._last_seen
    def get_last_hash_time(self):
        return self._last_hash_time
    def get_first_seen(self):
        return self._first_seen
    def get_saved_timestamp(self):
        return self._saved_timestamp
    def __repr__(self):
        returned = self._filename
        if self._hostname is not None:
            returned = "{}:{}".format(self._hostname, returned)
        return returned
