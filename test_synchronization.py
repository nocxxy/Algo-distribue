import threading
import time
from Process import Process

def test_synchronization():
    """Test de la synchronisation entre nœuds"""
    
    # Créer 3 processus
    processes = []
    for i in range(3):
        process = Process(f"TestNode{i}")
        processes.append(process)
    
    # Attendre que l'élection soit terminée
    print("=== Attente de l'élection du leader ===")
    time.sleep(10)
    
    # Trouver le leader
    leader = None
    for process in processes:
        if process.communication.state == NodeState.LEADER:
            leader = process
            break
    
    if leader:
        print(f"=== Leader trouvé: Nœud {leader.getId()} ===")
        
        # Test de synchronisation
        print("=== Test de synchronisation ===")
        
        def sync_callback():
            print(f"Nœud {leader.getId()} - Synchronisation terminée dans le callback!")
        
        # Démarrer la synchronisation depuis le leader
        success = leader.communication.synchronize(callback=sync_callback)
        if success:
            print(f"Synchronisation démarrée par le leader {leader.getId()}")
            
            # Attendre que la synchronisation se termine
            timeout = 10  # 10 secondes maximum
            start_time = time.time()
            
            while leader.communication.is_synchronizing and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if not leader.communication.is_synchronizing:
                print("✅ Synchronisation réussie!")
            else:
                print("❌ Timeout de synchronisation")
        else:
            print("❌ Échec du démarrage de la synchronisation")
    else:
        print("❌ Aucun leader trouvé")
    
    # Test de synchronisation depuis un follower
    print("\n=== Test de synchronisation depuis un follower ===")
    follower = None
    for process in processes:
        if process.communication.state == NodeState.FOLLOWER:
            follower = process
            break
    
    if follower:
        print(f"Follower trouvé: Nœud {follower.getId()}")
        
        def follower_sync_callback():
            print(f"Nœud {follower.getId()} - Synchronisation terminée dans le callback!")
        
        success = follower.communication.synchronize(callback=follower_sync_callback)
        if success:
            print(f"Synchronisation démarrée par le follower {follower.getId()}")
            
            # Attendre que la synchronisation se termine
            timeout = 10  # 10 secondes maximum
            start_time = time.time()
            
            while follower.communication.is_synchronizing and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if not follower.communication.is_synchronizing:
                print("✅ Synchronisation réussie!")
            else:
                print("❌ Timeout de synchronisation")
        else:
            print("❌ Échec du démarrage de la synchronisation")
    
    # Attendre un peu avant d'arrêter
    time.sleep(3)
    
    # Arrêter tous les processus
    print("\n=== Arrêt des processus ===")
    for process in processes:
        process.stop()
    
    for process in processes:
        process.waitStopped()
    
    print("Test terminé")

if __name__ == "__main__":
    # Import nécessaire pour les tests
    from State.NodeState import NodeState
    
    test_synchronization()