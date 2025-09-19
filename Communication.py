# Communication.py
from pyeventbus3.pyeventbus3 import *
from threading import Lock, Timer
from Message import *
from State import *
from time import time, sleep
import random

class Communication:

    def __init__(self):
        # Identifiants
        self.id = None              # ID du processus (permanent)
        self.temp_id = random.randint(10000, 99999)  # ID temporaire pour l'initialisation
        self.lamportClock = 0       # Horloge de Lamport
        
        # Communication
        self.mailbox = []           # File des messages reçus
        self.mailbox_lock = Lock()  # Verrou pour thread-safety
        self.world = set()          # Ensemble des nœuds connus (IDs permanents)
        self.temp_world = set()     # Ensemble des nœuds temporaires découverts
        
        # État et machine à états
        self.alive = True
        self.state = NodeState.FOLLOWER  # État initial
        self.state_machine = None        # Implémentation spécifique de l'état

        # Variables Raft persistantes
        self.current_term = 0      # Terme actuel (incrémente de façon monotone)
        self.voted_for = None      # Pour qui on a voté dans le terme actuel
        self.leader_id = None      # ID du leader actuel
        
        # Votes reçus pendant l'élection
        self.votes_received = set()
        
        # Timers et état d'initialisation
        self.discovery_timer = None
        self.registration_timer = None
        self.is_registered = False

    def init(self):
        """Initialise la communication et démarre le processus de découverte"""
        PyBus.Instance().register(self, self)
        self.transition_to_state(NodeState.FOLLOWER)
        self.start_discovery_phase()
    
    def start_discovery_phase(self):
        """Phase 1: Découverte des nœuds avec message Alive"""
        print(f"Nœud (temp_id: {self.temp_id}) démarre la phase de découverte")
        
        # Envoyer un message Alive
        alive_msg = AliveMessage(self.temp_id, self.get_lamport_timestamp())
        self.broadcast_message(alive_msg)

        if self.alive:
            # Attendre 3 secondes pour la découverte, puis tenter l'enregistrement
            self.discovery_timer = Timer(3.0, self.start_registration_phase)
            self.discovery_timer.start()
    
    def start_registration_phase(self):
        """Phase 2: Tentative d'enregistrement auprès du leader"""
        if self.alive:
            print(f"Nœud (temp_id: {self.temp_id}) tente l'enregistrement")
            if self.leader_id:
                # Il y a un leader connu, demander l'enregistrement
                registration_req = RegistrationRequest(self.temp_id, self.get_lamport_timestamp())
                self.send_message_to(self.leader_id, registration_req)
                
                # Attendre 5 secondes pour une réponse
                self.registration_timer = Timer(5.0, self.start_leader_election_phase)
                self.registration_timer.start()
            else:
                # Pas de leader connu, attendre un peu plus pour les heartbeats potentiels
                print(f"Nœud (temp_id: {self.temp_id}) attend des heartbeats...")
                self.registration_timer = Timer(3.0, self.start_leader_election_phase)
                self.registration_timer.start()
    
    def start_leader_election_phase(self):
        """Phase 3: Distribution d'ID puis démarrage de l'élection de leader"""
        if not self.is_registered:
            print(f"Nœud (temp_id: {self.temp_id}) aucun leader trouvé - démarre distribution d'ID")
            self.distribute_ids()
    
    def distribute_ids(self):
        """Phase 3.1: Auto-distribution des IDs aux nœuds découverts"""
        # Ajouter soi-même au monde temporaire
        self.temp_world.add(self.temp_id)
        
        # Trier pour avoir un ordre déterministe
        temp_nodes = sorted(list(self.temp_world))
        
        # Créer le mapping temp_id -> permanent_id
        id_mapping = {}
        for i, temp_id in enumerate(temp_nodes, 1):
            id_mapping[temp_id] = i
        
        print(f"Nœud {self.temp_id} calcule mapping d'ID: {id_mapping}")
        
        # Assigner son propre ID permanent
        self.id = id_mapping[self.temp_id]
        self.world = set(id_mapping.values())
        
        # Broadcaster la confirmation d'ID
        confirmation_msg = IdConfirmationMessage(
            self.temp_id,
            self.get_lamport_timestamp(),
            id_mapping
        )
        self.broadcast_message(confirmation_msg)
        
        # Marquer comme enregistré
        self.is_registered = True
        print(f"Nœud {self.temp_id} devient nœud {self.id}")
        print(f"Monde: {self.world}")
        
        # Attendre un peu que les autres nœuds reçoivent la confirmation
        Timer(1.0, self.start_election_after_id_distribution).start()
    
    def start_election_after_id_distribution(self):
        """Démarre l'élection après la distribution d'ID"""
        print(f"Nœud {self.id} démarre l'élection")
        self.transition_to_state(NodeState.CANDIDATE)
    
    def get_lamport_timestamp(self):
        """Retourne et incrémente l'horloge de Lamport"""
        self.lamportClock += 1
        return self.lamportClock
    
    def update_lamport_clock(self, received_timestamp):
        """Met à jour l'horloge de Lamport avec un timestamp reçu"""
        self.lamportClock = max(self.lamportClock, received_timestamp) + 1
    
    def transition_to_state(self, new_state):
        """Change l'état du nœud"""
        self.state = new_state
                
        # Créer la nouvelle machine à états
        if new_state == NodeState.FOLLOWER:
            self.state_machine = FollowerState(self)
        elif new_state == NodeState.CANDIDATE:
            self.state_machine = CandidateState(self)
        elif new_state == NodeState.LEADER:
            self.state_machine = LeaderState(self)
        
        # Entrer dans le nouvel état
        if self.state_machine:
            self.state_machine.enter_state()
    
    def send_message_to(self, target_id, message):
        """Envoie un message à un nœud spécifique"""
        # Simulation d'envoi - dans un vrai système, cela passerait par le réseau
        print(f"Envoi de {type(message).__name__} de {message.source} vers {target_id}")
        
        # Pour la simulation, on peut utiliser PyBus pour distribuer localement
        PyBus.Instance().post(message)
    
    def broadcast_message(self, message):
        """Diffuse un message à tous les nœuds connus"""
        print(f"Broadcast de {type(message).__name__} depuis {message.source}")
        PyBus.Instance().post(message)
    
    def _handle_message_common(self, message):
        """Logique commune pour tous les messages"""
        # Ignorer ses propres messages
        if message.source == self.id or message.source == self.temp_id:
            return
        
        # Mettre à jour l'horloge de Lamport
        self.update_lamport_clock(message.timestamp)
        
        # Traiter les messages spéciaux pour la phase d'initialisation
        if isinstance(message, RegistrationResponse) and not self.is_registered:
            self.handle_registration_response(message)
            return
        elif isinstance(message, WorldUpdateMessage):
            self.handle_world_update(message)
            return
        elif isinstance(message, HeartbeatMessage) and not self.is_registered:
            # Si on reçoit un heartbeat et qu'on n'est pas enregistré, demander l'enregistrement
            self.handle_heartbeat_during_initialization(message)
            return
        
        # Déléguer à la machine à états appropriée
        if self.state_machine:
            self.state_machine.handle_message(message)
    
    @subscribe(threadMode=Mode.PARALLEL, onEvent=AliveMessage)
    def handle_alive_message(self, message):
        """Gestionnaire pour les messages AliveMessage"""
        self._handle_message_common(message)
    
    @subscribe(threadMode=Mode.PARALLEL, onEvent=RegistrationRequest)
    def handle_registration_request_message(self, message):
        """Gestionnaire pour les messages RegistrationRequest"""
        self._handle_message_common(message)

    @subscribe(threadMode=Mode.PARALLEL, onEvent=RegistrationResponse)
    def handle_registration_response_message(self, message):
        """Gestionnaire pour les messages RegistrationResponse"""
        self._handle_message_common(message)

    @subscribe(threadMode=Mode.PARALLEL, onEvent=HeartbeatMessage)
    def handle_heartbeat_message(self, message):
        """Gestionnaire pour les messages HeartbeatMessage"""
        self._handle_message_common(message)

    @subscribe(threadMode=Mode.PARALLEL, onEvent=RequestVoteMessage)
    def handle_request_vote_message(self, message):
        """Gestionnaire pour les messages RequestVoteMessage"""
        self._handle_message_common(message)

    @subscribe(threadMode=Mode.PARALLEL, onEvent=VoteResponseMessage)
    def handle_vote_response_message(self, message):
        """Gestionnaire pour les messages VoteResponseMessage"""
        self._handle_message_common(message)

    @subscribe(threadMode=Mode.PARALLEL, onEvent=WorldUpdateMessage)
    def handle_world_update_message(self, message):
        """Gestionnaire pour les messages WorldUpdateMessage"""
        self._handle_message_common(message)
    
    @subscribe(threadMode=Mode.PARALLEL, onEvent=IdAnnouncementMessage)
    def handle_id_announcement_message(self, message):
        """Gestionnaire pour les messages IdAnnouncementMessage"""
        self._handle_message_common(message)
    
    @subscribe(threadMode=Mode.PARALLEL, onEvent=IdConfirmationMessage)
    def handle_id_confirmation_message(self, message):
        """Gestionnaire pour les messages IdConfirmationMessage"""
        self._handle_message_common(message)
    
    @subscribe(threadMode=Mode.PARALLEL, onEvent=WorldInfoMessage)
    def handle_world_info_message(self, message):
        """Gestionnaire pour les messages WorldInfoMessage"""
        self._handle_message_common(message)
    
    def handle_registration_response(self, message):
        """Traite la réponse d'enregistrement du leader"""
        if self.registration_timer:
            self.registration_timer.cancel()
        
        print(f"Nœud reçoit ID {message.assigned_id} du leader {message.source}")
        
        # Assigner l'ID permanent et mettre à jour le monde
        self.id = message.assigned_id
        self.world = message.world_nodes
        self.leader_id = message.source
        self.is_registered = True
        
        # Rester en état FOLLOWER
        print(f"Nœud {self.id} enregistré avec succès")
    
    def handle_world_update(self, message):
        """Traite une mise à jour du monde depuis le leader"""
        if message.source == self.leader_id:
            self.world = message.nodes
            print(f"Nœud {self.id} met à jour son monde: {self.world}")
    
    def handle_heartbeat_during_initialization(self, message):
        """Traite un heartbeat reçu pendant l'initialisation - demande l'enregistrement"""
        if not self.is_registered:
            print(f"Nœud (temp_id: {self.temp_id}) détecte un leader {message.source}, demande l'enregistrement")
            self.leader_id = message.source
            self.current_term = message.term
            
            # Annuler les timers existants
            if self.discovery_timer:
                self.discovery_timer.cancel()
            if self.registration_timer:
                self.registration_timer.cancel()
            
            # Demander l'enregistrement immédiatement
            registration_req = RegistrationRequest(self.temp_id, self.get_lamport_timestamp())
            self.send_message_to(self.leader_id, registration_req)
    
    def get_status(self):
        """Retourne le statut actuel du nœud (pour debug)"""
        return {
            'id': self.id,
            'temp_id': self.temp_id,
            'state': self.state.value,
            'term': self.current_term,
            'leader_id': self.leader_id,
            'world': list(self.world),
            'is_registered': self.is_registered
        }
    
    def addLetterMessage(self, message):
        """Ajoute un message à la boîte aux lettres"""
        with self.mailbox_lock:
            self.mailbox.append(message)

    def hasLetterMessage(self):
        """Vérifie s'il y a des messages dans la boîte aux lettres"""
        with self.mailbox_lock:
            return len(self.mailbox) > 0
        
    def retrieveLetterMessage(self):
        """Récupère et supprime le premier message de la boîte aux lettres"""
        with self.mailbox_lock:
            if self.mailbox:
                return self.mailbox.pop(0)
            else:
                return None
            
    def get_rank(self):
        """Retourne l'ID du nœud"""
        return self.id if self.id is not None else self.temp_id

    def stop(self):
        """Arrête la communication et les timers"""
        self.alive = False
        if self.discovery_timer:
            self.discovery_timer.cancel()
        if self.registration_timer:
            self.registration_timer.cancel()