"""
Exemple du nouveau système de heartbeat avec détection de pannes
"""

def explain_new_heartbeat_system():
    """Explique le nouveau système de heartbeat"""
    
    print("=== NOUVEAU SYSTÈME DE HEARTBEAT ===\n")
    
    print("🔄 CYCLE DE HEARTBEAT:")
    print("1. Leader envoie HeartbeatMessage en BROADCAST")
    print("   - Contient le terme actuel")
    print("   - Contient le monde connu (ex: {1,2,3})")
    print("   - Envoyé toutes les 3 secondes\n")
    
    print("2. Followers reçoivent le heartbeat:")
    print("   - Mettent à jour leur terme")
    print("   - Mettent à jour leur monde local")
    print("   - Répondent avec HeartbeatConfirmationMessage\n")
    
    print("3. Leader attend les confirmations (5 secondes):")
    print("   - Collecte les HeartbeatConfirmationMessage")
    print("   - Identifie les nœuds qui ne répondent pas")
    print("   - Retire les nœuds silencieux du monde\n")
    
    print("📊 EXEMPLE D'EXÉCUTION:")
    print("Monde initial: {1, 2, 3} (1=Leader, 2,3=Followers)\n")
    
    print("Cycle 1:")
    print("  Leader 1 -> Broadcast: HeartbeatMessage(terme=1, monde={1,2,3})")
    print("  Follower 2 -> Leader 1: HeartbeatConfirmationMessage(terme=1)")
    print("  Follower 3 -> Leader 1: HeartbeatConfirmationMessage(terme=1)")
    print("  ✅ Tous répondent, monde reste {1,2,3}\n")
    
    print("Cycle 2 (nœud 3 en panne):")
    print("  Leader 1 -> Broadcast: HeartbeatMessage(terme=1, monde={1,2,3})")
    print("  Follower 2 -> Leader 1: HeartbeatConfirmationMessage(terme=1)")
    print("  Follower 3 -> ❌ SILENCE (en panne)")
    print("  🔥 Leader 1 détecte panne de 3, nouveau monde={1,2}\n")
    
    print("Cycle 3:")
    print("  Leader 1 -> Broadcast: HeartbeatMessage(terme=1, monde={1,2})")
    print("  Follower 2 -> Reçoit monde mis à jour -> {1,2}")
    print("  Follower 2 -> Leader 1: HeartbeatConfirmationMessage(terme=1)")
    print("  ✅ Synchronisation terminée\n")
    
    print("💡 AVANTAGES:")
    print("✅ Détection automatique des pannes")
    print("✅ Mise à jour du monde en temps réel")
    print("✅ Synchronisation automatique entre tous les nœuds")
    print("✅ Pas de nœuds fantômes dans le système")
    print("✅ Robustesse face aux pannes")

def show_code_examples():
    """Montre des exemples de code pour le nouveau système"""
    
    print("\n=== EXEMPLES DE CODE ===\n")
    
    print("1. ENVOI DE HEARTBEAT (Leader):")
    print("""
def send_heartbeat(self):
    heartbeat = HeartbeatMessage(
        self.communication.id,
        self.communication.get_lamport_timestamp(),
        self.communication.current_term,
        self.communication.world.copy()  # ← Monde inclus
    )
    self.communication.broadcast_message(heartbeat)
    Timer(5.0, self.check_heartbeat_responses).start()
""")
    
    print("2. RÉPONSE AU HEARTBEAT (Follower):")
    print("""
def handle_heartbeat(self, message):
    # Mettre à jour le monde local
    self.communication.world = message.world_nodes.copy()
    
    # Envoyer confirmation si vivant
    if self.communication.alive:
        confirmation = HeartbeatConfirmationMessage(
            self.communication.id,
            self.communication.get_lamport_timestamp(),
            self.communication.current_term
        )
        self.communication.send_message_to(message.source, confirmation)
""")
    
    print("3. DÉTECTION DE PANNES (Leader):")
    print("""
def check_heartbeat_responses(self):
    expected = self.communication.world - {self.communication.id}
    missing = expected - self.heartbeat_confirmations
    
    if missing:
        print(f"Nœuds en panne détectés: {missing}")
        for failed_node in missing:
            self.communication.world.discard(failed_node)
""")

if __name__ == '__main__':
    explain_new_heartbeat_system()
    show_code_examples()