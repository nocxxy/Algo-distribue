from dataclasses import dataclass
from .AbstractMessage import AbstractMessage

@dataclass
class HeartbeatMessage(AbstractMessage):
    """Heartbeat du leader"""
    def __init__(self, source, timestamp, term: int):
        super().__init__(source, timestamp)
        self.term = term