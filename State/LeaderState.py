from .StateMachine import StateMachine
from .NodeState import NodeState
from Message import *
from threading import Timer

class LeaderState(StateMachine):
    
    def __init__(self, communication):
        super().__init__(communication)
        self.heartbeat_timer = None
        self.heartbeat_interval = 3  # Envoyer un heartbeat toutes les 3 secondes
        self.heartbeat_timeout = 5   # Timeout pour les confirmations
        self.next_node_id = max(self.communication.world) + 1 if self.communication.world else 1
        self.heartbeat_confirmations = set()  # Confirmations reçues pour le heartbeat actuel
        self.waiting_for_confirmations = False
    
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
    
    def cleanup(self):
        """Nettoie les timers avant de quitter l'état LEADER"""
        if self.heartbeat_timer:
            self.heartbeat_timer.cancel()
            self.heartbeat_timer = None
    
    def start_heartbeat(self):
        """Démarre l'envoi régulier de heartbeats"""
        if not self.communication.alive:
            print(f"Leader {self.communication.id} arrêté, pas de heartbeat")
            return
            
        self.send_heartbeat()
        # Programmer le prochain heartbeat seulement si toujours vivant
        if self.communication.alive:
            self.heartbeat_timer = Timer(self.heartbeat_interval, self.start_heartbeat)
            self.heartbeat_timer.start()
    
    def send_heartbeat(self):
        """Envoie un heartbeat en broadcast avec le monde connu"""
        if not self.communication.alive:
            print(f"Leader {self.communication.id} arrêté, pas d'envoi de heartbeat")
            return
            
        print(f"Leader {self.communication.id} envoie heartbeat avec monde: {self.communication.world}")
        
        # Réinitialiser les confirmations pour ce cycle
        self.heartbeat_confirmations = set()
        self.waiting_for_confirmations = True
        
        # Créer le heartbeat avec le monde actuel
        heartbeat = HeartbeatMessage(
            self.communication.id,
            self.communication.get_lamport_timestamp(),
            self.communication.current_term,
            self.communication.world.copy()  # Inclure le monde connu
        )
        
        # Envoyer en broadcast
        self.communication.broadcast_message(heartbeat)
        
        # Programmer le timeout pour vérifier les confirmations seulement si vivant
        if self.communication.alive:
            Timer(self.heartbeat_timeout, self.check_heartbeat_responses).start()
    
    def check_heartbeat_responses(self):
        """Vérifie les réponses de heartbeat et met à jour le monde"""
        # Vérifier si le nœud est toujours vivant
        if not self.communication.alive or not self.waiting_for_confirmations:
            return
        
        self.waiting_for_confirmations = False
        
        # Nœuds qui devraient répondre (tous sauf le leader)
        expected_responses = self.communication.world - {self.communication.id}
        
        # Nœuds qui n'ont pas répondu
        missing_nodes = expected_responses - self.heartbeat_confirmations
        
        if missing_nodes:
            print(f"Leader {self.communication.id} détecte des nœuds en panne: {missing_nodes}")
            
            # Retirer les nœuds en panne du monde
            for failed_node in missing_nodes:
                self.communication.world.discard(failed_node)
            
            print(f"Nouveau monde après détection de pannes: {self.communication.world}")
            
            # Si le leader est seul, on peut le laisser continuer ou l'arrêter
            # Pour éviter la boucle infinie, on continue normalement
        else:
            print(f"Leader {self.communication.id} reçoit confirmations de tous les nœuds: {self.heartbeat_confirmations}")
    
    def handle_message(self, message):
        """Traite les messages reçus en tant que LEADER"""
        match message:
            case VoteResponseMessage() | HeartbeatMessage():
                return  # Ignorer les réponses de vote et les heartbeats des autres leaders
            case HeartbeatConfirmationMessage():
                self.handle_heartbeat_confirmation(message)
            case RequestVoteMessage():
                self.handle_vote_request(message)
            case RegistrationRequest():
                self.handle_registration_request(message)
            case AliveMessage():
                self.handle_new_node_discovery(message)
            case _:
                self.communication.addLetterMessage(message)
    
    def handle_heartbeat_confirmation(self, message):
        """Traite une confirmation de heartbeat d'un follower"""
        if self.waiting_for_confirmations:
            self.heartbeat_confirmations.add(message.source)
            print(f"Leader {self.communication.id} reçoit confirmation de {message.source}")
    
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