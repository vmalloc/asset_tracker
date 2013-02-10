class File(object):
    def __init__(self, hostname, filename, file_hash, file_timestamp):
        super(File, self).__init__()
        self._hostname = hostname
        self._filename = filename
        self._hash = file_hash
        self._last_seen = None
        self._saved_timestamp = file_timestamp
    def get_filename(self):
        return self._filename
    def get_hash(self):
        return self._hash
    def set_hash(self, h):
        self._hash = h
    def notify_seen(self, when):
        self._last_seen = when
    def get_last_seen(self):
        return self._last_seen
    def get_saved_timestamp(self):
        return self._saved_timestamp
    def __repr__(self):
        returned = self._filename
        if self._hostname is not None:
            returned = "{}:{}".format(self._hostname, returned)
        return returned
