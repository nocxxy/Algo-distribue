from AbstactMessage import AbstractMessage

class BroadcastMessage(AbstractMessage):
    def __init__(self, timestamp, source, content):
        super().__init__(timestamp)
        self.source = source
        self.content = content

    def get_source(self):
        return self.source

    def get_content(self):
        return self.content