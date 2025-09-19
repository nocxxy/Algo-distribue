from dataclasses import dataclass
from .AbstractMessage import AbstractMessage

@dataclass
class HeartbeatConfirmationMessage(AbstractMessage):
    """Confirmation qu'un nœud est en vie en réponse à un heartbeat"""
    def __init__(self, source, timestamp, term: int, target=None):
        super().__init__(source, timestamp, target)
        self.term = term
        self.is_system_message = True  # Message système