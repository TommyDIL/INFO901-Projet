class Message:
    def __init__(self, timestamp: int, content, sender_id: int, recipient_id: int = None):
        self.timestamp: int = timestamp
        self.content = content
        self.sender_id = sender_id
        self.recipient_id = recipient_id
