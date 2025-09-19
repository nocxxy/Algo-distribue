from .AbstractMessage import AbstractMessage
from dataclasses import dataclass

@dataclass
class SynchronizeMessage(AbstractMessage):
    """Message pour initier la synchronisation"""
    def __init__(self, source, timestamp, target=None):
        super().__init__(source, timestamp, target)
        self.is_system_message = True  # Message système qui peut être traité pendant la synchronisation

@dataclass
class SynchronizeConfirmedMessage(AbstractMessage):
    """Message de confirmation de synchronisation envoyé au leader"""
    def __init__(self, source, timestamp, target=None):
        super().__init__(source, timestamp, target)
        self.is_system_message = True  # Message système qui peut être traité pendant la synchronisation

@dataclass
class AllSynchronizedMessage(AbstractMessage):
    """Message broadcast par le leader pour signaler que tous les nœuds sont synchronisés"""
    def __init__(self, source, timestamp, target=None):
        super().__init__(source, timestamp, target)
        self.is_system_message = True  # Message système qui peut être traité pendant la synchronisation