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
        self.alive = True  # Flag pour arrêter proprement les timers
        
        # Synchronisation
        self.is_synchronizing = False  # Flag pour indiquer que le nœud est en cours de synchronisation
        self.synchronize_confirmations = set()  # Set des confirmations reçues pour la synchronisation
        self.synchronize_callback = None  # Callback à appeler quand la synchronisation est terminée
        
        # BroadcastSync
        self.broadcast_sync_waiting = {}  # Dict: {from_id: {'payload': payload, 'callback': callback, 'acks': set()}}
        self.broadcast_sync_lock = Lock()  # Verrou pour thread-safety du broadcast sync
        
        # SendToSync / ReceiveFromSync
        self.send_to_sync_waiting = {}  # Dict: {sync_id: {'event': Event, 'callback': callback}}
        self.receive_from_sync_waiting = {}  # Dict: {from_id: {'sync_id': sync_id, 'event': Event, 'payload': None, 'callback': callback}}
        self.send_to_sync_lock = Lock()  # Verrou pour thread-safety
        self.sync_id_counter = 0  # Compteur pour générer des IDs uniques

        self.request = False
        self.release = True
        self.token = None
        self.token_lock = Lock()  # Verrou pour l'accès au jeton
        self.have_token = False

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
        # Nettoyer l'ancien état et annuler ses timers
        if self.state_machine:
            self.state_machine.cleanup()
        
        old_state = self.state
        self.state = new_state
        
        print(f"Nœud {self.id or self.temp_id} transition {old_state.value} -> {new_state.value}")
        
        # Créer la nouvelle machine à états
        match new_state:
            case NodeState.FOLLOWER:
                self.state_machine = FollowerState(self)
            case NodeState.CANDIDATE:
                self.state_machine = CandidateState(self)
            case NodeState.LEADER:
                self.state_machine = LeaderState(self)
        
        # Entrer dans le nouvel état
        if self.state_machine:
            self.state_machine.enter_state()
    
    def send_message_to(self, target_id, message):
        """Envoie un message à un nœud spécifique"""
        # Ne pas s'envoyer de message à soi-même
        if target_id == self.id or target_id == self.temp_id:
            return
            
        # Marquer le message comme ciblé
        message.target = target_id
        
        # Simulation d'envoi - dans un vrai système, cela passerait par le réseau
        print(f"Envoi de {type(message).__name__} de {message.source} vers {target_id}")
        
        # Pour la simulation, on utilise PyBus mais avec un target spécifique
        PyBus.Instance().post(message)
    
    def broadcast_message(self, message):
        """Diffuse un message à tous les nœuds connus"""
        # Marquer explicitement comme broadcast
        message.target = None
        print(f"Broadcast de {type(message).__name__} depuis {message.source}")
        PyBus.Instance().post(message)
    
    def _handle_message_common(self, message):
        """Logique commune pour tous les messages"""
        # Ignorer ses propres messages - vérifier à la fois l'ID permanent et temporaire
        if (message.source == self.id or 
            message.source == self.temp_id or 
            (hasattr(message, 'source') and message.source in [self.id, self.temp_id])):
            return False
        
        # Vérifier si le message est destiné à ce nœud
        if not message.is_for_me(self.id) and not message.is_for_me(self.temp_id):
            # Message pas pour nous, l'ignorer
            return False
        
        # Mettre à jour l'horloge de Lamport
        self.update_lamport_clock(message.timestamp)
        
        # Traiter les messages spéciaux pour la phase d'initialisation
        match message:
            case RegistrationResponse() if not self.is_registered:
                self.handle_registration_response(message)
                return True
            case WorldUpdateMessage():
                self.handle_world_update(message)
                return True
            case HeartbeatMessage() if not self.is_registered:
                # Si on reçoit un heartbeat et qu'on n'est pas enregistré, demander l'enregistrement
                self.handle_heartbeat_during_initialization(message)
                return True
            case SynchronizeMessage():
                self.handle_synchronize_message(message)
                return True
            case SynchronizeConfirmedMessage():
                self.handle_synchronize_confirmed_message(message)
                return True
            case AllSynchronizedMessage():
                self.handle_all_synchronized_message(message)
                return True
            case BroadcastSyncMessage():
                self.handle_broadcast_sync_message(message)
                return True
            case BroadcastSyncAckMessage():
                self.handle_broadcast_sync_ack_message(message)
                return True
            case SendToSyncMessage():
                self.handle_send_to_sync_message(message)
                return True
            case SendToSyncAckMessage():
                self.handle_send_to_sync_ack_message(message)
                return True
            case _:
                # Déléguer à la machine à états appropriée
                if self.state_machine:
                    self.state_machine.handle_message(message)
                    return True
        
        return False
    
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

    @subscribe(threadMode=Mode.PARALLEL, onEvent=HeartbeatConfirmationMessage)
    def handle_heartbeat_confirmation_message(self, message):
        """Gestionnaire pour les messages HeartbeatConfirmationMessage"""
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
    
    @subscribe(threadMode=Mode.PARALLEL, onEvent=SynchronizeMessage)
    def handle_synchronize_message_subscribe(self, message):
        """Gestionnaire pour les messages SynchronizeMessage"""
        self._handle_message_common(message)
    
    @subscribe(threadMode=Mode.PARALLEL, onEvent=SynchronizeConfirmedMessage)
    def handle_synchronize_confirmed_message_subscribe(self, message):
        """Gestionnaire pour les messages SynchronizeConfirmedMessage"""
        self._handle_message_common(message)
    
    @subscribe(threadMode=Mode.PARALLEL, onEvent=AllSynchronizedMessage)
    def handle_all_synchronized_message_subscribe(self, message):
        """Gestionnaire pour les messages AllSynchronizedMessage"""
        self._handle_message_common(message)
    
    @subscribe(threadMode=Mode.PARALLEL, onEvent=BroadcastSyncMessage)
    def handle_broadcast_sync_message_subscribe(self, message):
        """Gestionnaire pour les messages BroadcastSyncMessage"""
        self._handle_message_common(message)
    
    @subscribe(threadMode=Mode.PARALLEL, onEvent=BroadcastSyncAckMessage)
    def handle_broadcast_sync_ack_message_subscribe(self, message):
        """Gestionnaire pour les messages BroadcastSyncAckMessage"""
        self._handle_message_common(message)
    
    @subscribe(threadMode=Mode.PARALLEL, onEvent=SendToSyncMessage)
    def handle_send_to_sync_message_subscribe(self, message):
        """Gestionnaire pour les messages SendToSyncMessage"""
        self._handle_message_common(message)
    
    @subscribe(threadMode=Mode.PARALLEL, onEvent=SendToSyncAckMessage)
    def handle_send_to_sync_ack_message_subscribe(self, message):
        """Gestionnaire pour les messages SendToSyncAckMessage"""
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
    
    def handle_synchronize_message(self, message):
        """
        Traite un message SynchronizeMessage.
        Si c'est un follower, envoie une confirmation au leader.
        Si c'est le leader, commence à attendre les confirmations.
        """
        print(f"Nœud {self.id} reçoit demande de synchronisation de {message.source}")
        
        if self.state == NodeState.LEADER:
            # Le leader a reçu sa propre demande de synchronisation
            # Commencer à attendre les confirmations de tous les autres nœuds
            expected_nodes = self.world - {self.id}  # Tous les nœuds sauf lui-même
            print(f"Leader {self.id} attend confirmations de: {expected_nodes}")
        else:
            # Les followers envoient une confirmation au leader
            if self.leader_id:
                confirm_msg = SynchronizeConfirmedMessage(
                    self.id, 
                    self.get_lamport_timestamp(), 
                    target=self.leader_id
                )
                self.send_message_to(self.leader_id, confirm_msg)
                print(f"Nœud {self.id} envoie confirmation de synchronisation au leader {self.leader_id}")
    
    def handle_synchronize_confirmed_message(self, message):
        """
        Traite un message SynchronizeConfirmedMessage (seulement pour le leader).
        Quand toutes les confirmations sont reçues, envoie AllSynchronizedMessage.
        """
        if self.state != NodeState.LEADER:
            print(f"Nœud {self.id} reçoit confirmation de synchronisation mais n'est pas leader")
            return
            
        print(f"Leader {self.id} reçoit confirmation de synchronisation de {message.source}")
        self.synchronize_confirmations.add(message.source)
        
        # Vérifier si on a toutes les confirmations
        expected_nodes = self.world - {self.id}  # Tous les nœuds sauf le leader
        if self.synchronize_confirmations >= expected_nodes:
            print(f"Leader {self.id} a reçu toutes les confirmations - envoie AllSynchronizedMessage")
            
            # Envoyer le message de fin de synchronisation en broadcast
            all_sync_msg = AllSynchronizedMessage(self.id, self.get_lamport_timestamp())
            self.broadcast_message(all_sync_msg)
            
            # Le leader se synchronise aussi
            self._complete_synchronization()
    
    def handle_all_synchronized_message(self, message):
        """
        Traite un message AllSynchronizedMessage.
        Signale que la synchronisation est terminée.
        """
        print(f"Nœud {self.id} reçoit signal de fin de synchronisation du leader {message.source}")
        self._complete_synchronization()
    
    def _complete_synchronization(self):
        """Termine le processus de synchronisation"""
        self.is_synchronizing = False
        self.synchronize_confirmations.clear()
        
        # Appeler le callback si défini
        if self.synchronize_callback:
            callback = self.synchronize_callback
            self.synchronize_callback = None
            callback()
        
        print(f"Nœud {self.id} synchronisation terminée")
    
    def handle_broadcast_sync_message(self, message):
        """
        Traite un message BroadcastSyncMessage.
        Récepteur: reçoit le message et envoie un ACK à l'émetteur.
        """
        from_id = message.original_sender
        payload = message.payload
        
        print(f"Nœud {self.id} reçoit broadcastSync de {from_id}: {payload}")
        
        # Envoyer un ACK à l'émetteur
        ack_msg = BroadcastSyncAckMessage(
            self.id,
            self.get_lamport_timestamp(),
            from_id,
            target=from_id  # Envoyer directement à l'émetteur
        )
        self.send_message_to(from_id, ack_msg)
        
        # Débloquer l'attente si on était en attente de ce message
        with self.broadcast_sync_lock:
            if from_id in self.broadcast_sync_waiting:
                sync_info = self.broadcast_sync_waiting[from_id]
                sync_info['payload'] = payload
                sync_info['received'] = True
                
                # Appeler le callback si défini
                if sync_info['callback']:
                    callback = sync_info['callback']
                    callback(payload)
                
                # Débloquer l'attente
                sync_info['event'].set()
                
                # Nettoyer
                del self.broadcast_sync_waiting[from_id]
    
    def handle_broadcast_sync_ack_message(self, message):
        """
        Traite un message BroadcastSyncAckMessage.
        Émetteur: reçoit un ACK d'un récepteur.
        """
        from_id = message.original_sender
        ack_from = message.source
        
        print(f"Nœud {self.id} reçoit ACK de {ack_from} pour broadcastSync de {from_id}")
        
        # Si je ne suis pas l'émetteur original, ignorer
        if self.id != from_id:
            return
        
        with self.broadcast_sync_lock:
            if from_id in self.broadcast_sync_waiting:
                sync_info = self.broadcast_sync_waiting[from_id]
                sync_info['acks'].add(ack_from)
                
                # Vérifier si on a tous les ACKs
                if sync_info['acks'] >= sync_info['expected_acks']:
                    print(f"Nœud {self.id} a reçu tous les ACKs pour broadcastSync")
                    
                    # Appeler le callback si défini
                    if sync_info['callback']:
                        callback = sync_info['callback']
                        callback(sync_info['payload'])
                    
                    # Débloquer l'attente
                    sync_info['event'].set()
                    
                    # Nettoyer
                    del self.broadcast_sync_waiting[from_id]
    
    def handle_send_to_sync_message(self, message):
        """
        Traite un message SendToSyncMessage.
        Récepteur: reçoit le message et envoie un ACK à l'expéditeur.
        """
        from_id = message.source
        sync_id = message.sync_id
        payload = message.payload
        
        print(f"Nœud {self.id} reçoit sendToSync de {from_id} (sync_id: {sync_id}): {payload}")
        
        # Envoyer un ACK à l'expéditeur
        ack_msg = SendToSyncAckMessage(
            self.id,
            self.get_lamport_timestamp(),
            sync_id,
            target=from_id
        )
        self.send_message_to(from_id, ack_msg)
        
        # Vérifier si quelqu'un attend ce message
        with self.send_to_sync_lock:
            if from_id in self.receive_from_sync_waiting:
                wait_info = self.receive_from_sync_waiting[from_id]
                wait_info['payload'] = payload
                wait_info['sync_id'] = sync_id
                
                # Appeler le callback si défini
                if wait_info['callback']:
                    callback = wait_info['callback']
                    callback(payload)
                
                # Débloquer l'attente
                wait_info['event'].set()
                # Note: on ne supprime pas de receive_from_sync_waiting ici,
                # c'est fait dans receiveFromSync pour récupérer le payload
    
    def handle_send_to_sync_ack_message(self, message):
        """
        Traite un message SendToSyncAckMessage.
        Expéditeur: reçoit l'ACK du récepteur.
        """
        sync_id = message.sync_id
        ack_from = message.source
        
        print(f"Nœud {self.id} reçoit ACK de {ack_from} pour sendToSync (sync_id: {sync_id})")
        
        with self.send_to_sync_lock:
            if sync_id in self.send_to_sync_waiting:
                wait_info = self.send_to_sync_waiting[sync_id]
                
                # Appeler le callback si défini
                if wait_info['callback']:
                    callback = wait_info['callback']
                    callback()
                
                # Débloquer l'attente
                wait_info['event'].set()
                # Note: on ne supprime pas de send_to_sync_waiting ici,
                # c'est fait dans sendToSync pour nettoyer
    
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
    
    def synchronize(self, callback=None):
        """
        Démarre le processus de synchronisation.
        Le processus est bloqué jusqu'à ce que tous les nœuds soient synchronisés.
        
        Args:
            callback: Fonction à appeler quand la synchronisation est terminée (optionnel)
        """
        if self.is_synchronizing:
            print(f"Nœud {self.id} est déjà en cours de synchronisation")
            return False
            
        print(f"Nœud {self.id} démarre la synchronisation")
        self.is_synchronizing = True
        self.synchronize_callback = callback
        self.synchronize_confirmations.clear()
        
        # Envoyer le message de synchronisation en broadcast
        sync_msg = SynchronizeMessage(self.id, self.get_lamport_timestamp())
        self.broadcast_message(sync_msg)
        
        return True
    
    def broadcastSync(self, payload, from_id, callback=None):
        """
        Broadcast synchrone selon les spécifications:
        - Si le processus a l'identifiant 'from_id', il envoie le message à tous les autres 
          processus et attend que tous les autres aient reçu le message
        - Si le processus n'a pas l'identifiant 'from_id', il attend de recevoir le message de 'from_id'
        
        Args:
            payload: Le contenu du message à broadcaster
            from_id: L'identifiant de l'émetteur
            callback: Fonction à appeler quand l'opération est terminée (optionnel)
            
        Returns:
            True si l'opération a été démarrée avec succès, False sinon
        """
        import threading
        
        if self.id == from_id:
            # Je suis l'émetteur
            print(f"Nœud {self.id} démarre broadcastSync en tant qu'émetteur")
            
            with self.broadcast_sync_lock:
                # Vérifier qu'on n'a pas déjà un broadcast en cours pour ce from_id
                if from_id in self.broadcast_sync_waiting:
                    print(f"Nœud {self.id} a déjà un broadcastSync en cours pour l'émetteur {from_id}")
                    return False
                
                # Initialiser l'état d'attente
                expected_acks = self.world - {self.id}  # Tous les nœuds sauf moi
                self.broadcast_sync_waiting[from_id] = {
                    'payload': payload,
                    'callback': callback,
                    'acks': set(),
                    'expected_acks': expected_acks,
                    'event': threading.Event()
                }
            
            # Envoyer le message en broadcast
            broadcast_msg = BroadcastSyncMessage(
                self.id,
                self.get_lamport_timestamp(),
                payload,
                from_id
            )
            self.broadcast_message(broadcast_msg)
            
            # Si on a un callback, on ne bloque pas
            if callback:
                return True
            
            # Sinon, attendre que tous les nœuds aient acquitté
            event = self.broadcast_sync_waiting[from_id]['event']
            event.wait()  # Bloquant jusqu'à ce que tous les ACKs soient reçus
            
            return True
            
        else:
            # Je suis un récepteur - attendre le message de from_id
            print(f"Nœud {self.id} attend broadcastSync de l'émetteur {from_id}")
            
            with self.broadcast_sync_lock:
                # Si on a déjà une attente pour ce from_id, rejoindre l'attente existante
                if from_id not in self.broadcast_sync_waiting:
                    self.broadcast_sync_waiting[from_id] = {
                        'payload': None,
                        'callback': callback,
                        'acks': set(),
                        'expected_acks': set(),
                        'event': threading.Event(),
                        'received': False
                    }
            
            # Si on a un callback, on ne bloque pas
            if callback:
                return True
            
            # Sinon, attendre de recevoir le message
            event = self.broadcast_sync_waiting[from_id]['event']
            event.wait()  # Bloquant jusqu'à réception du message
            
            return True
    
    def sendToSync(self, payload, dest_id, callback=None):
        """
        Envoie un message de manière synchrone à un destinataire spécifique.
        Bloque jusqu'à ce que le destinataire ait reçu le message.
        
        Args:
            payload: Le contenu du message à envoyer
            dest_id: L'identifiant du destinataire
            callback: Fonction à appeler quand l'ACK est reçu (optionnel)
            
        Returns:
            True si l'envoi a réussi, False en cas d'erreur ou d'arrêt
        """
        import threading
        
        if not self.alive:
            print(f"Nœud {self.id} arrêté - sendToSync annulé")
            return False
            
        if dest_id not in self.world:
            print(f"Nœud {self.id} - destinataire {dest_id} inconnu")
            return False
        
        # Générer un ID unique pour cette communication
        with self.send_to_sync_lock:
            self.sync_id_counter += 1
            sync_id = f"{self.id}-{dest_id}-{self.sync_id_counter}"
        
        print(f"Nœud {self.id} démarre sendToSync vers {dest_id} (sync_id: {sync_id})")
        
        # Préparer l'attente de l'ACK
        event = threading.Event()
        with self.send_to_sync_lock:
            self.send_to_sync_waiting[sync_id] = {
                'event': event,
                'callback': callback,
                'dest_id': dest_id
            }
        
        # Envoyer le message
        sync_msg = SendToSyncMessage(
            self.id,
            self.get_lamport_timestamp(),
            payload,
            sync_id,
            target=dest_id
        )
        self.send_message_to(dest_id, sync_msg)
        
        # Si on a un callback, on ne bloque pas
        if callback:
            return True
        
        # Sinon, attendre l'ACK ou l'arrêt du système
        if not self.alive:
            return False
            
        success = event.wait(timeout=30)  # Timeout de 30 secondes
        
        # Nettoyer
        with self.send_to_sync_lock:
            if sync_id in self.send_to_sync_waiting:
                del self.send_to_sync_waiting[sync_id]
        
        if not success:
            print(f"Nœud {self.id} - timeout sendToSync vers {dest_id}")
            return False
        
        return True
    
    def receiveFromSync(self, from_id, callback=None):
        """
        Attend de recevoir un message synchrone d'un expéditeur spécifique.
        Bloque jusqu'à ce que le message arrive.
        
        Args:
            from_id: L'identifiant de l'expéditeur attendu
            callback: Fonction à appeler avec le payload reçu (optionnel)
            
        Returns:
            Le payload reçu, ou None en cas d'erreur ou d'arrêt
        """
        import threading
        
        if not self.alive:
            print(f"Nœud {self.id} arrêté - receiveFromSync annulé")
            return None
            
        if from_id not in self.world:
            print(f"Nœud {self.id} - expéditeur {from_id} inconnu")
            return None
        
        print(f"Nœud {self.id} attend receiveFromSync de {from_id}")
        
        # Préparer l'attente du message
        event = threading.Event()
        with self.send_to_sync_lock:
            self.receive_from_sync_waiting[from_id] = {
                'event': event,
                'payload': None,
                'callback': callback,
                'sync_id': None
            }
        
        # Si on a un callback, on ne bloque pas
        if callback:
            return True
        
        # Sinon, attendre le message ou l'arrêt du système
        if not self.alive:
            return None
            
        success = event.wait(timeout=30)  # Timeout de 30 secondes
        
        # Récupérer le payload
        payload = None
        with self.send_to_sync_lock:
            if from_id in self.receive_from_sync_waiting:
                payload = self.receive_from_sync_waiting[from_id]['payload']
                del self.receive_from_sync_waiting[from_id]
        
        if not success:
            print(f"Nœud {self.id} - timeout receiveFromSync de {from_id}")
            return None
        
        return payload
    
    def addLetterMessage(self, message):
        """
        Ajoute un message à la boîte aux lettres.
        Si le nœud est en cours de synchronisation, seuls les messages système sont acceptés.
        """
        # Si on est en cours de synchronisation, ne traiter que les messages système
        if self.is_synchronizing and not message.is_system():
            print(f"Nœud {self.id} en synchronisation - message non-système ignoré: {type(message).__name__}")
            return
            
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
        """Arrête proprement la communication et nettoie les ressources"""
        self.alive = False
        
        # Nettoyer les timers
        if self.discovery_timer:
            self.discovery_timer.cancel()
        if self.registration_timer:
            self.registration_timer.cancel()
        
        # Débloquer toutes les attentes synchrones
        self._cleanup_sync_operations()
        
        # Nettoyer l'état actuel
        if self.state_machine:
            self.state_machine.cleanup()
        
        print(f"Nœud {self.id or self.temp_id} arrêté proprement")
    
    def _cleanup_sync_operations(self):
        """Nettoie et débloque toutes les opérations synchrones en cours"""
        # Débloquer sendToSync
        with self.send_to_sync_lock:
            for sync_id, wait_info in self.send_to_sync_waiting.items():
                wait_info['event'].set()
            self.send_to_sync_waiting.clear()
            
            # Débloquer receiveFromSync
            for from_id, wait_info in self.receive_from_sync_waiting.items():
                wait_info['event'].set()
            self.receive_from_sync_waiting.clear()
        
        # Débloquer broadcastSync
        with self.broadcast_sync_lock:
            for from_id, sync_info in self.broadcast_sync_waiting.items():
                sync_info['event'].set()
            self.broadcast_sync_waiting.clear()

    def sendToken(self):
        """Envoie le token au prochain voisin dans le monde"""
        if not self.world or self.id is None:
            print("Nœud n'a pas de voisins ou d'ID assigné")
            return
        
        # Trier les IDs pour déterminer l'ordre circulaire
        sorted_world = sorted(self.world)
        my_index = sorted_world.index(self.id)
        
        # Trouver le prochain voisin dans l'ordre circulaire
        next_index = (my_index + 1) % len(sorted_world)
        next_neighbor = sorted_world[next_index]
        
        # Créer et envoyer le message de token
        with self.token_lock:
            token_id = self.token
            self.token = None  # Libérer le token localement

        if self.alive:
            print("------------------------------------------------")
            print("-----------------ENVOIE DU TOKEN---------------")
            print("------------------------------------------------")
            self.have_token = False
            token_msg = TokenMessage(self.id, self.get_lamport_timestamp(), token_id=token_id)
            self.send_message_to(next_neighbor, token_msg)
            print(f"Nœud {self.id} envoie le token au voisin {next_neighbor}")

    def requestToken(self):
        self.request = True
        self.release = False
        print("------------------------------------------------")
        print("-----------------DEMANDE DU TOKEN---------------")
        print("------------------------------------------------")
        while not self.have_token and self.alive:
            sleep(1)  # Attente active, peut être optimisée avec des événements
        print(f"Nœud {self.id} a reçu le token {self.have_token}")
        return

    def releaseToken(self):
        print("------------------------------------------------")
        print("-----------------RELEASE DU TOKEN---------------")
        print("------------------------------------------------")
        self.request = False
        self.release = True
        return

    @subscribe(threadMode=Mode.PARALLEL, onEvent=TokenMessage)
    def handle_token_message(self, message):
        """Gestionnaire pour les messages TokenMessage"""
        if (message.target != self.id):
            return  # Message pas pour nous
        if self.request:
            with self.token_lock:
                self.token = message.token_id
                self.have_token = True
        
        while not self.release and self.alive:
            sleep(1)
        if self.alive:
            self.sendToken()

    def init_token_ring(self):
        if self.state == NodeState.LEADER and self.world:
            # Le leader initialise le token
            self.token = random.randint(1000, 9999)  # ID de token aléatoire
            self.have_token = True
            print(f"Leader {self.id} initialise le token: {self.token}")
            self.sendToken()
