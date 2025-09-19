from dataclasses import dataclass
from .AbstractMessage import AbstractMessage

@dataclass
class SendToSyncMessage(AbstractMessage):
    """Message pour communication synchrone point-à-point"""
    def __init__(self, source, timestamp, payload, sync_id, target=None):
        super().__init__(source, timestamp, target)
        self.payload = payload  # Le contenu du message à envoyer
        self.sync_id = sync_id  # ID unique pour identifier cette communication sync
        self.is_system_message = True  # Message système

@dataclass
class SendToSyncAckMessage(AbstractMessage):
    """Message d'acquittement pour communication synchrone point-à-point"""
    def __init__(self, source, timestamp, sync_id, target=None):
        super().__init__(source, timestamp, target)
        self.sync_id = sync_id  # ID unique pour identifier cette communication sync
        self.is_system_message = True  # Message système