from enum import Enum

class NodeState(Enum):
    """Les trois états possibles d'un nœud dans Raft"""
    FOLLOWER = "FOLLOWER"    # Suit un leader existant
    CANDIDATE = "CANDIDATE"  # Candidat à l'élection
    LEADER = "LEADER"        # Leader élu qui dirige le cluster