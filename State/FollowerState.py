from .StateMachine import StateMachine
from .NodeState import NodeState
from Message import *
from threading import Timer
import random

class FollowerState(StateMachine):
    
    def __init__(self, communication):
        super().__init__(communication)
        self.heartbeat_timeout = None
        self.election_timeout = random.uniform(5, 10)  # Timeout aléatoire pour éviter les elections simultanées
    
    def enter_state(self):
        """Entrée dans l'état FOLLOWER"""
        print(f"Nœud {self.communication.id or self.communication.temp_id} entre en état FOLLOWER (terme {self.communication.current_term})")
        self.reset_election_timeout()
    
    def cleanup(self):
        """Nettoie les timers avant de quitter l'état FOLLOWER"""
        if self.heartbeat_timeout:
            self.heartbeat_timeout.cancel()
            self.heartbeat_timeout = None
    
    def reset_election_timeout(self):
        """Remet à zéro le timeout d'élection"""
        if self.heartbeat_timeout:
            self.heartbeat_timeout.cancel()
        
        if self.communication.alive:
            self.heartbeat_timeout = Timer(self.election_timeout, self.on_timeout)
            self.heartbeat_timeout.start()
    
    def handle_message(self, message):
        """Traite les messages reçus en tant que FOLLOWER"""

        match message:
            case HeartbeatMessage():
                self.handle_heartbeat(message)
                return
            case RequestVoteMessage():
                self.handle_vote_request(message)
                return
            case RegistrationRequest():
                return  # Ignorer les demandes d'enregistrement en tant que FOLLOWER
            case AliveMessage():
                self.handle_alive_message(message)
                return
            case IdAnnouncementMessage():
                self.handle_id_announcement(message)
                return
            case IdConfirmationMessage():
                self.handle_id_confirmation(message)
                return
            case _:
                self.communication.addLetterMessage(message)
                return
          
    def handle_heartbeat(self, message):
        """Traite un heartbeat du leader"""
        # Vérifier que ce n'est pas notre propre heartbeat
        if message.source == self.communication.id or message.source == self.communication.temp_id:
            return
            
        if message.term >= self.communication.current_term:
            self.communication.current_term = message.term
            self.communication.leader_id = message.source
            self.communication.voted_for = None  # Reset du vote
            self.reset_election_timeout()
            print(f"Nœud {self.communication.id or self.communication.temp_id} reçoit heartbeat du leader {message.source} (terme {message.term})")
        elif message.term < self.communication.current_term:
            print(f"Nœud {self.communication.id or self.communication.temp_id} ignore heartbeat obsolète du nœud {message.source} (terme {message.term} < {self.communication.current_term})")
    
    def handle_vote_request(self, message):
        """Traite une demande de vote"""
        vote_granted = False
        
        if (message.term > self.communication.current_term and 
            (self.communication.voted_for is None or self.communication.voted_for == message.candidate_id)):
            
            self.communication.current_term = message.term
            self.communication.voted_for = message.candidate_id
            vote_granted = True
            self.reset_election_timeout()
            print(f"Nœud {self.communication.id} vote pour {message.candidate_id}")
        
        # Répondre au candidat
        response = VoteResponseMessage(
            self.communication.id,
            self.communication.get_lamport_timestamp(),
            self.communication.current_term,
            vote_granted
        )
        self.communication.send_message_to(message.source, response)
    
    def handle_alive_message(self, message):
        """Traite un message Alive pour découverte des nœuds"""
        # Ajouter le nœud temporaire au monde temporaire
        temp_world = getattr(self.communication, 'temp_world', set())
        temp_world.add(message.source)
        self.communication.temp_world = temp_world
        print(f"Nœud {self.communication.temp_id} découvre le nœud temporaire {message.source}")
    
    def handle_id_announcement(self, message):
        """Traite une annonce d'ID pendant la phase de distribution"""
        print(f"Nœud {self.communication.temp_id} reçoit annonce d'ID {message.proposed_id} de {message.temp_id}")
        # Cette logique sera gérée par le leader lors de la distribution
        
    def handle_id_confirmation(self, message):
        """Traite la confirmation de distribution d'ID"""
        if self.communication.temp_id in message.id_mapping:
            old_temp_id = self.communication.temp_id
            self.communication.id = message.id_mapping[self.communication.temp_id]
            self.communication.world = set(message.id_mapping.values())
            self.communication.is_registered = True
            print(f"Nœud {old_temp_id} reçoit ID permanent {self.communication.id}")
            print(f"Monde final: {self.communication.world}")
    
    def on_timeout(self):
        """Timeout d'élection - lance la phase de distribution d'ID puis devient candidat"""
        if not self.communication.is_registered and hasattr(self.communication, 'temp_world') and self.communication.alive:
            print(f"Nœud {self.communication.temp_id} timeout d'élection - lance distribution d'ID puis élection")
            self.communication.distribute_ids()
        if self.communication.alive:
            # Devenir candidat après distribution d'ID
            print(f"Nœud {self.communication.id} devient CANDIDAT")
            self.communication.transition_to_state(NodeState.CANDIDATE)