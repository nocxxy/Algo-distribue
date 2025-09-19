from dataclasses import dataclass
from .AbstractMessage import AbstractMessage

@dataclass
class BroadcastMessage(AbstractMessage):
    def __init__(self, timestamp, source, content):
        super().__init__(source, timestamp)
        self.content = content

    def get_content(self):
        return self.content