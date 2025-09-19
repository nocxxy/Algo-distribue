from dataclasses import dataclass
from .AbstractMessage import AbstractMessage
from typing import Set

@dataclass
class RegistrationRequest(AbstractMessage):
    """Demande d'enregistrement au leader"""
    def __init__(self, source, timestamp, target=None):
        super().__init__(source, timestamp, target)

@dataclass
class RegistrationResponse(AbstractMessage):
    """Réponse d'enregistrement avec ID assigné"""
    def __init__(self, source, timestamp, assigned_id: int, world_nodes: Set[int], target=None):
        super().__init__(source, timestamp, target)
        self.assigned_id = assigned_id
        self.world_nodes = world_nodes