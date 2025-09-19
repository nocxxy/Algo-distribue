from dataclasses import dataclass
from .AbstractMessage import AbstractMessage

@dataclass
class TokenMessage(AbstractMessage):
    """Message contenant le jeton pour la section critique distribuée"""
    def __init__(self, source, timestamp, token_id, target=None):
        super().__init__(source, timestamp, target)
        self.token_id = token_id  # ID unique du jeton
        self.is_system_message = True  # Message système - n'impacte pas l'horloge Lamport

