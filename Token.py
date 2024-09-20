from Message import *

class Token:
    def __init__(self, receiver: int):
        self.receiver = receiver

from enum import Enum

class TokenStatus(Enum):
    NONE = 0
    REQUESTED = 1
    POSSESSED = 2
    RELEASED = 3