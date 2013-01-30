import os
import pushy
import subprocess

def setUp():
    _initialize_pushy()

def tearDown():
    pass

def get_pushy_connection():
    return _pushy_conn

def get_local_connection():
    return LocalConnection()

class LocalConnection(object):
    class modules(object):
        import os
        import tempfile
        import __builtin__

def _initialize_pushy():
    global _pushy_conn
    _pushy_conn = pushy.connect(
        "ssh:127.0.0.1", port=2222, username="vagrant", use_native=False,
        key_filename=os.path.expanduser("~/.vagrant.d/insecure_private_key")
    )

def _execute(cmd):
    result = subprocess.call(
        cmd, shell=True,
        cwd=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    assert result == 0, "Command {} failed".format(cmd)
