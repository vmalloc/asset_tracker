class Call(object):
    def __init__(_self, *args, **kwargs):
        super(Call, _self).__init__()
        _self._args = args
        _self._kwargs = kwargs
    def apply(self, f, *args, **kwargs):
        final_args = list(args) + list(self._args)
        final_kwargs = dict(self._kwargs)
        final_kwargs.update(kwargs)
        return f(*final_args, **final_kwargs)
