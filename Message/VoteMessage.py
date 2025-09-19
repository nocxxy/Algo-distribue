from dataclasses import dataclass
from .AbstractMessage import AbstractMessage

@dataclass
class RequestVoteMessage(AbstractMessage):
    """Demande de vote pour l'élection"""
    def __init__(self, source, timestamp, term: int, candidate_id: int, target=None):
        super().__init__(source, timestamp, target)
        self.term = term
        self.candidate_id = candidate_id
        self.is_system_message = True  # Message système

@dataclass
class VoteResponseMessage(AbstractMessage):
    """Réponse de vote"""
    def __init__(self, source, timestamp, term: int, vote_granted: bool, target=None):
        super().__init__(source, timestamp, target)
        self.term = term
        self.vote_granted = vote_granted
        self.is_system_message = True  # Message système