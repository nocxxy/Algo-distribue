from dataclasses import dataclass
from .AbstractMessage import AbstractMessage

@dataclass
class RequestVoteMessage(AbstractMessage):
    """Demande de vote pour l'élection"""
    def __init__(self, source, timestamp, term: int, candidate_id: int):
        super().__init__(source, timestamp)
        self.term = term
        self.candidate_id = candidate_id

@dataclass
class VoteResponseMessage(AbstractMessage):
    """Réponse de vote"""
    def __init__(self, source, timestamp, term: int, vote_granted: bool):
        super().__init__(source, timestamp)
        self.term = term
        self.vote_granted = vote_granted