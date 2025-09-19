from dataclasses import dataclass
from .AbstractMessage import AbstractMessage

@dataclass
class BroadcastSyncMessage(AbstractMessage):
    """Message pour broadcast synchrone - contient le payload et l'émetteur"""
    def __init__(self, source, timestamp, payload, original_sender, target=None):
        super().__init__(source, timestamp, target)
        self.payload = payload  # Le contenu du message à broadcaster
        self.original_sender = original_sender  # L'émetteur original (from)
        self.is_system_message = True  # Message système pour ne pas être bloqué

@dataclass
class BroadcastSyncAckMessage(AbstractMessage):
    """Message d'acquittement pour broadcast synchrone"""
    def __init__(self, source, timestamp, original_sender, target=None):
        super().__init__(source, timestamp, target)
        self.original_sender = original_sender  # L'émetteur original du broadcast
        self.is_system_message = True  # Message système