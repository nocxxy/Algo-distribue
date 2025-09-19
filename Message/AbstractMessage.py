from dataclasses import dataclass

@dataclass
class AbstractMessage:
    def __init__(self, source, timestamp, target=None):
        self.source = source
        self.timestamp = timestamp
        self.target = target  # None pour broadcast, ID spécifique pour send_to
    
    def get_timestamp(self):
        return self.timestamp

    def get_source(self):
        return self.source
    
    def get_target(self):
        return self.target
    
    def is_broadcast(self):
        """Retourne True si c'est un message broadcast, False si ciblé"""
        return self.target is None
    
    def is_for_me(self, my_id):
        """Vérifie si ce message est destiné à ce nœud"""
        return self.target is None or self.target == my_id