import threading


class ChangeFeed:
    """Revision counter for the documented single-server process deployment."""

    def __init__(self):
        self._revision = 0
        self._lock = threading.Lock()

    def publish(self):
        with self._lock:
            self._revision += 1

    def revision(self) -> int:
        with self._lock:
            return self._revision
