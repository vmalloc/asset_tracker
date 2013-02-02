class Call(object):
    def __init__(_self, *args, **kwargs):
        super(Call, _self).__init__()
        _self._args = args
        _self._kwargs = kwargs
    def apply(self, f):
        return f(*self._args, **self._kwargs)
