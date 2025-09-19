from dataclasses import dataclass
from .AbstractMessage import AbstractMessage

@dataclass
class AliveMessage(AbstractMessage):
    """Message de découverte des nœuds"""
    def __init__(self, source, timestamp, target=None):
        super().__init__(source, timestamp, target)