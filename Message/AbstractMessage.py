from dataclasses import dataclass

@dataclass
class AbstractMessage:
    def __init__(self, source, timestamp):
        self.source = source
        self.timestamp = timestamp
    
    def get_timestamp(self):
        return self.timestamp

    def get_source(self):
        return self.source