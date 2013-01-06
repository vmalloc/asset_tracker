class Alert(object):
    def __init__(self, asset, msg):
        super(Alert, self).__init__()
        self.asset = asset
        self.msg = msg
    def __repr__(self):
        return "{}: {}".format(self.asset.get_filenames().keys()[0], self.msg)
