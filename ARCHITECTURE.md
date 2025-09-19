# Élection de Leader et Auto-Distribution d'ID

## Vue d'ensemble

Ce système implémente l'élection de leader et l'auto-distribution d'ID pour une architecture distribuée en utilisant le pattern État et le protocole Raft.

## Processus complet étape par étape

### Phase 1: Découverte des nœuds (AliveMessage)

1. **Nœuds 1, 2, 3 créés simultanément**

   - Chaque nœud génère un `temp_id` aléatoire (ex: 12345, 67890, 54321)
   - Ils commencent tous en état `FOLLOWER`

2. **Broadcast de messages Alive**
   - Chaque nœud envoie `AliveMessage(temp_id, timestamp)`
   - Ils découvrent mutuellement leurs `temp_id`
   - Création de `temp_world = {12345, 67890, 54321}`

### Phase 2: Tentative d'enregistrement

1. **Recherche de leader existant**

   - Les nœuds attendent 3 secondes pour découvrir un leader
   - Comme aucun leader n'existe, `leader_id = None`

2. **Timeout et passage à la distribution d'ID**
   - Après 5 secondes sans réponse de leader
   - Déclenchement de `start_leader_election_phase()`

### Phase 3: Auto-distribution d'ID

1. **Calcul déterministe des IDs**

   ```python
   temp_nodes = sorted([12345, 67890, 54321])  # [12345, 54321, 67890]
   id_mapping = {
       12345: 1,  # Premier dans l'ordre -> ID 1
       54321: 2,  # Deuxième dans l'ordre -> ID 2
       67890: 3   # Troisième dans l'ordre -> ID 3
   }
   ```

2. **Broadcast de confirmation**
   - Envoi de `IdConfirmationMessage(temp_id, timestamp, id_mapping)`
   - Tous les nœuds reçoivent le même mapping
   - Assignation des IDs permanents : `id = id_mapping[temp_id]`

### Phase 4: Élection Raft

1. **Démarrage de l'élection**

   - Timeout des FOLLOWERS → transition vers CANDIDATE
   - Le candidat incrémente son terme et vote pour lui-même

2. **Demandes de vote**

   ```python
   # Candidat envoie à tous
   RequestVoteMessage(candidate_id, timestamp, term, candidate_id)
   ```

3. **Réponses de vote**

   ```python
   # Followers répondent
   VoteResponseMessage(source, timestamp, term, vote_granted=True/False)
   ```

4. **Élection du leader**
   - Majoritaire (2 votes sur 3 dans notre exemple)
   - Le gagnant devient LEADER et envoie des heartbeats

### Phase 5: Enregistrement des nouveaux nœuds

1. **Nœud 4 rejoint**

   - Génère son `temp_id` (ex: 98765)
   - Envoie `AliveMessage(98765, timestamp)`

2. **Leader détecte le nouveau nœud**

   - Reçoit le message Alive
   - Attend une `RegistrationRequest`

3. **Enregistrement**

   ```python
   # Nœud 4 → Leader
   RegistrationRequest(98765, timestamp)

   # Leader → Nœud 4
   RegistrationResponse(leader_id, timestamp, assigned_id=4, world_nodes={1,2,3,4})
   ```

4. **Mise à jour du monde**
   ```python
   # Leader → Tous les autres nœuds
   WorldUpdateMessage(leader_id, timestamp, world_nodes={1,2,3,4})
   ```

## États et transitions

```
FOLLOWER → (timeout + pas de leader) → Auto-distribution ID → CANDIDATE → (majorité votes) → LEADER
    ↑                                                                         ↓
    ← (terme plus récent ou heartbeat)  ←  ←  ←  ←  ←  ←  ←  ←  ←  ←  ←  ←  ←  ←
```

## Architecture des classes

### Messages

- `AliveMessage`: Découverte mutuelle
- `RegistrationRequest/Response`: Enregistrement nouveaux nœuds
- `RequestVoteMessage/VoteResponseMessage`: Élection Raft
- `HeartbeatMessage`: Maintien autorité leader
- `IdConfirmationMessage`: Confirmation distribution ID
- `WorldUpdateMessage`: Mise à jour du monde

### États (Pattern State)

- `FollowerState`: État par défaut, écoute heartbeats
- `CandidateState`: Mène l'élection, demande votes
- `LeaderState`: Gère les heartbeats et nouveaux nœuds

## Utilisation

```python
# Créer les nœuds
node1 = Process("Node-1")
node2 = Process("Node-2")
node3 = Process("Node-3")

# Attendre l'élection (≈10 secondes)
time.sleep(10)

# Ajouter un nouveau nœud
node4 = Process("Node-4")  # S'enregistre automatiquement

# Vérifier l'état
status = node1.communication.get_status()
print(f"Nœud 1: {status}")
```

## Test

Exécutez le script de test :

```bash
python test_leader_election.py
```

Ce test simule le scénario complet avec création simultanée, élection, et ajout d'un nouveau nœud.
