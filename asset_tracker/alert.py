class Alert(object):
    def __init__(self, asset):
        super(Alert, self).__init__()
        self.asset = asset

class DeletionAlert(Alert):
    def __repr__(self):
        return "** DELETED: {}".format(self.asset)

class ChangeAlert(Alert):
    def __init__(self, asset, old_hash, new_hash):
        super(ChangeAlert, self).__init__(asset)
        self.old_hash = old_hash
        self.new_hash = new_hash
    def __repr__(self):
        return "** CHANGED: {}".format(self.asset)
