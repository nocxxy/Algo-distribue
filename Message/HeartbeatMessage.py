from dataclasses import dataclass
from .AbstractMessage import AbstractMessage
from typing import Set

@dataclass
class HeartbeatMessage(AbstractMessage):
    """Heartbeat du leader avec le monde connu"""
    def __init__(self, source, timestamp, term: int, world_nodes: Set[int], target=None):
        super().__init__(source, timestamp, target)
        self.term = term
        self.world_nodes = world_nodes  # Monde connu par le leader
        self.is_system_message = True  # Message système