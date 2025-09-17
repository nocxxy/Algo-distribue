class AbstractMessage:
    def __init__(self, timestamp):
        self.timestamp = timestamp
    
    def get_timestamp(self):
        return self.timestamp