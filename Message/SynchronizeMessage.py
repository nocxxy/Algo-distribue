from .AbstractMessage import AbstractMessage
from dataclasses import dataclass

@dataclass
class SynchronizeMessage(AbstractMessage):
    """Message de synchronisation de l'état du monde"""
    def __init__(self, source, timestamp, world_nodes: set, target=None):
        super().__init__(source, timestamp, target)
        self.world_nodes = world_nodes  # Ensemble des nœuds connus par l'expéditeur

@dataclass
class SynchronizeConfirmMessage(AbstractMessage):
    """Message de confirmation de la synchronisation"""
    def __init__(self, source, timestamp, target=None):
        super().__init__(source, timestamp, target)

@dataclass
class AllSynchronizedMessage(AbstractMessage):
    """Message indiquant que tous les nœuds sont synchronisés"""
    def __init__(self, source, timestamp, target=None):
        super().__init__(source, timestamp, target)