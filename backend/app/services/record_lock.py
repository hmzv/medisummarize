"""Serialize in-process record extraction/index writes in this prototype worker.

This is not a distributed lock; multi-worker deployments need database/job locks.
"""
from contextlib import contextmanager
from threading import Lock, RLock
from weakref import WeakValueDictionary

_guard = Lock()
_locks = WeakValueDictionary()


@contextmanager
def record_write_lock(record_id):
    with _guard:
        lock = _locks.get(record_id)
        if lock is None:
            lock = RLock()
            _locks[record_id] = lock
    with lock:
        yield
