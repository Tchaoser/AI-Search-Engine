# backend/sandbox.py
import os
import subprocess
from contextlib import contextmanager

@contextmanager
def block_shell_execution():
    """Temporarily block subprocess/os.system inside this context."""
    orig_popen = subprocess.Popen
    orig_run = subprocess.run
    orig_system = os.system

    def _blocked(*_a, **_kw):
        raise PermissionError("Shell execution blocked")

    subprocess.Popen = _blocked
    subprocess.run = _blocked
    os.system = _blocked
    try:
        yield
    finally:
        subprocess.Popen = orig_popen
        subprocess.run = orig_run
        os.system = orig_system
