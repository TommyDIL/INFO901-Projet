from threading import Lock, Thread

class Lamport:
    def __init__(self):
        self.clock: int = 0
        self.mutex = Lock()

    def increment_clock(self) -> None:
        with self.mutex:
            self.clock += 1

    def set_lamport_clock(self, timestamp: int) -> None:
        with self.mutex:
            self.clock = max(int(self.clock), int(timestamp))
