from dataclasses import dataclass
from .AbstractMessage import AbstractMessage
from typing import Dict

@dataclass
class IdAnnouncementMessage(AbstractMessage):
    """Message d'annonce d'ID pour l'auto-distribution"""
    def __init__(self, source, timestamp, proposed_id: int, temp_id: int):
        super().__init__(source, timestamp)
        self.proposed_id = proposed_id  # ID proposé pour ce nœud
        self.temp_id = temp_id         # ID temporaire actuel

@dataclass
class IdConfirmationMessage(AbstractMessage):
    """Message de confirmation de l'attribution d'ID"""
    def __init__(self, source, timestamp, id_mapping: Dict[int, int]):
        super().__init__(source, timestamp)
        self.id_mapping = id_mapping   # Mapping temp_id -> assigned_id

@dataclass
class WorldInfoMessage(AbstractMessage):
    """Message contenant les informations du monde connu"""
    def __init__(self, source, timestamp, world_nodes: set):
        super().__init__(source, timestamp)
        self.world_nodes = world_nodes