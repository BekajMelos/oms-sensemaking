from threading import RLock


class RuntimeSettings:
    def __init__(self):
        self._lock = RLock()

    def get(self, key):
        from oms_sensemaking.config import SETTINGS  # lazy import

        with self._lock:
            return getattr(SETTINGS, key)

    def set(self, key, value):
        from oms_sensemaking.config import SETTINGS  # lazy import

        with self._lock:
            setattr(SETTINGS, key, value)

    def bulk_set(self, updates: dict):
        for k, v in updates.items():
            self.set(k, v)


RUNTIME_SETTINGS = RuntimeSettings()
