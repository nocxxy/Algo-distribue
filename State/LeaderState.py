from .StateMachine import StateMachine
from .NodeState import NodeState
from Message import *
from threading import Timer

class LeaderState(StateMachine):
    
    def __init__(self, communication):
        super().__init__(communication)
        self.heartbeat_timer = None
        self.heartbeat_interval = 2  # Envoyer un heartbeat toutes les 2 secondes
        self.next_node_id = max(self.communication.world) + 1 if self.communication.world else 1
    
    def enter_state(self):
        """Entrée dans l'état LEADER"""
        self.communication.leader_id = self.communication.id
        print(f"Nœud {self.communication.id} devient LEADER (terme {self.communication.current_term})")
        
        # Assurer que l'ID du leader est dans le monde
        if self.communication.id:
            self.communication.world.add(self.communication.id)
            if self.communication.id >= self.next_node_id:
                self.next_node_id = self.communication.id + 1
        
        self.start_heartbeat()
    
    def start_heartbeat(self):
        """Démarre l'envoi régulier de heartbeats"""
        if self.communication.alive:
            self.send_heartbeat()
            self.heartbeat_timer = Timer(self.heartbeat_interval, self.start_heartbeat)
            self.heartbeat_timer.start()

    
    def send_heartbeat(self):
        """Envoie un heartbeat à tous les followers"""
        heartbeat = HeartbeatMessage(
            self.communication.id,
            self.communication.get_lamport_timestamp(),
            self.communication.current_term
        )
        for node_id in self.communication.world:
            if node_id != self.communication.id:
                self.communication.send_message_to(node_id, heartbeat)
    
    def handle_message(self, message):
        """Traite les messages reçus en tant que LEADER"""
        if isinstance(message, (VoteResponseMessage, HeartbeatMessage)):
            return  # Ignorer les réponses de vote et les heartbeats des autres leaders
        elif isinstance(message, RequestVoteMessage):
            self.handle_vote_request(message)
        elif isinstance(message, RegistrationRequest):
            self.handle_registration_request(message)
        elif isinstance(message, AliveMessage):
            self.handle_new_node_discovery(message)
        else:
            self.communication.addLetterMessage(message)
    
    def handle_registration_request(self, message):
        """Traite une demande d'enregistrement d'un nouveau nœud"""
        # Assigner un nouvel ID
        new_id = self.next_node_id
        self.next_node_id += 1
        
        # Ajouter le nouveau nœud au monde
        self.communication.world.add(new_id)
        
        print(f"Leader {self.communication.id} assigne l'ID {new_id} au nœud {message.source}")
        
        # Répondre avec l'ID assigné et l'état du monde
        response = RegistrationResponse(
            self.communication.id,
            self.communication.get_lamport_timestamp(),
            new_id,
            self.communication.world.copy()
        )
        
        self.communication.send_message_to(message.source, response)
        
        # Informer tous les autres nœuds de la mise à jour du monde
        world_update = WorldUpdateMessage(
            self.communication.id,
            self.communication.get_lamport_timestamp(),
            self.communication.world.copy()
        )
        
        for node_id in self.communication.world:
            if node_id != self.communication.id and node_id != new_id:
                self.communication.send_message_to(node_id, world_update)
    
    def handle_vote_request(self, message):
        """Un leader ne vote pas, sauf si le terme est plus récent"""
        if message.term > self.communication.current_term:
            # Terme plus récent, redevenir follower
            self.communication.current_term = message.term
            if self.heartbeat_timer:
                self.heartbeat_timer.cancel()
            self.communication.transition_to_state(NodeState.FOLLOWER)
            
            # Voter pour le candidat
            self.communication.voted_for = message.candidate_id
            response = VoteResponseMessage(
                self.communication.id,
                self.communication.get_lamport_timestamp(),
                self.communication.current_term,
                True
            )
            self.communication.send_message_to(message.source, response)
    
    def handle_alive_message(self, message):
        """Traite un message Alive - ajouter le nœud au monde s'il n'y est pas"""
        if message.source not in self.communication.world:
            self.communication.world.add(message.source)
            print(f"Leader {self.communication.id} découvre le nœud {message.source}")
    
    def handle_new_node_discovery(self, message):
        """Traite la découverte d'un nouveau nœud qui envoie AliveMessage"""
        print(f"Leader {self.communication.id} détecte un nouveau nœud avec temp_id {message.source}")
        
        # Le nouveau nœud devrait ensuite envoyer un RegistrationRequest
        # On ne fait rien de spécial ici, on attend la demande d'enregistrement
    
    def stop_heartbeat(self):
        """Arrête l'envoi de heartbeats"""
        if self.heartbeat_timer:
            self.heartbeat_timer.cancel()
    
    def on_timeout(self):
        """Un leader n'a pas de timeout particulier"""
        pass