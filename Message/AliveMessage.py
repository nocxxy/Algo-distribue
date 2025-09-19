from dataclasses import dataclass
from .AbstractMessage import AbstractMessage

@dataclass
class AliveMessage(AbstractMessage):
    """Message de découverte des nœuds"""
    def __init__(self, source, timestamp):
        super().__init__(source, timestamp)