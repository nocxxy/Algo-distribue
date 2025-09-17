from Message.Message import *

test = BroadcastMessage(1, "source", "content")
print(test.get_content())