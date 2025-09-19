from dataclasses import dataclass
from .AbstractMessage import AbstractMessage
from typing import Set

@dataclass
class WorldUpdateMessage(AbstractMessage):
    """Mise à jour du monde connu"""
    def __init__(self, source, timestamp, nodes: Set[int]):
        super().__init__(source, timestamp)
        self.nodes = nodes