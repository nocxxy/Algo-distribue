from .StateMachine import StateMachine
from .NodeState import NodeState
from Message import *
from threading import Timer
import random

class CandidateState(StateMachine):
    
    def __init__(self, communication):
        super().__init__(communication)
        self.election_timeout = None
        self.election_timeout_duration = random.uniform(5, 10)
    
    def enter_state(self):
        """Entrée dans l'état CANDIDATE"""
        self.start_election()
    
    def cleanup(self):
        """Nettoie les timers avant de quitter l'état CANDIDATE"""
        if self.election_timeout:
            self.election_timeout.cancel()
            self.election_timeout = None
    
    def start_election(self):
        """Démarre une nouvelle élection"""
        # Vérifier si le nœud est toujours vivant
        if not self.communication.alive:
            print(f"Nœud {self.communication.id} arrêté, pas d'élection")
            return
            
        # Si on est seul, devenir leader directement
        if len(self.communication.world) <= 1:
            print(f"Nœud {self.communication.id} seul dans le monde, devient leader directement")
            self.communication.transition_to_state(NodeState.LEADER)
            return
        
        # Incrémenter le terme et voter pour soi-même
        self.communication.current_term += 1
        self.communication.voted_for = self.communication.id
        self.communication.votes_received = {self.communication.id}
        
        print(f"Nœud {self.communication.id} démarre une élection (terme {self.communication.current_term})")
        
        # Envoyer des demandes de vote à tous les nœuds connus
        vote_request = RequestVoteMessage(
            self.communication.id,
            self.communication.get_lamport_timestamp(),
            self.communication.current_term,
            self.communication.id
        )
        
        for node_id in self.communication.world:
            if node_id != self.communication.id:
                self.communication.send_message_to(node_id, vote_request)
        
        # Démarrer le timeout d'élection
        self.reset_election_timeout()
    
    def reset_election_timeout(self):
        """Remet à zéro le timeout d'élection"""
        if self.election_timeout:
            self.election_timeout.cancel()
        
        self.election_timeout = Timer(self.election_timeout_duration, self.on_timeout)
        self.election_timeout.start()
    
    def handle_message(self, message):
        """Traite les messages reçus en tant que CANDIDATE"""
        match message:
            case VoteResponseMessage():
                self.handle_vote_response(message)
                return
            case HeartbeatMessage():
                self.handle_heartbeat(message)
                return
            case RequestVoteMessage():
                self.handle_vote_request(message)
                return
            case _:
                self.communication.addLetterMessage(message)
                return
        
    
    def handle_vote_response(self, message):
        """Traite une réponse de vote"""
        # Ignorer ses propres réponses
        if message.source == self.communication.id or message.source == self.communication.temp_id:
            return
            
        if message.term > self.communication.current_term:
            # Terme plus récent, redevenir follower
            self.communication.current_term = message.term
            self.communication.transition_to_state(NodeState.FOLLOWER)
            return
        
        if message.term == self.communication.current_term and message.vote_granted:
            self.communication.votes_received.add(message.source)
            print(f"Nœud {self.communication.id} reçoit vote de {message.source} ({len(self.communication.votes_received)} votes)")
            
            # Vérifier si on a la majorité
            majority = (len(self.communication.world) // 2) + 1
            print(f"Majorité requise: {majority}, monde: {self.communication.world}")
            
            if len(self.communication.votes_received) >= majority:
                print(f"Nœud {self.communication.id} élu LEADER avec {len(self.communication.votes_received)} votes sur {len(self.communication.world)} nœuds")
                self.communication.transition_to_state(NodeState.LEADER)
    
    def handle_heartbeat(self, message):
        """Si on reçoit un heartbeat d'un leader légitime, redevenir follower"""
        if message.term >= self.communication.current_term:
            self.communication.current_term = message.term
            self.communication.leader_id = message.source
            
            # Mettre à jour le monde avec celui reçu du leader
            if hasattr(message, 'world_nodes') and message.world_nodes:
                self.communication.world = message.world_nodes.copy()
                print(f"Candidat {self.communication.id} met à jour son monde: {self.communication.world}")
            
            print(f"Candidat {self.communication.id} reconnaît le leader {message.source}")
            self.communication.transition_to_state(NodeState.FOLLOWER)
    
    def handle_vote_request(self, message):
        """Traite une demande de vote d'un autre candidat"""
        if message.term > self.communication.current_term:
            # Terme plus récent, redevenir follower et voter
            self.communication.current_term = message.term
            self.communication.voted_for = message.candidate_id
            self.communication.transition_to_state(NodeState.FOLLOWER)
            
            response = VoteResponseMessage(
                self.communication.id,
                self.communication.get_lamport_timestamp(),
                self.communication.current_term,
                True
            )
            self.communication.send_message_to(message.source, response)
    
    def on_timeout(self):
        """Timeout d'élection - recommencer une élection"""
        print(f"Nœud {self.communication.id} timeout d'élection - recommence")
        self.start_election()