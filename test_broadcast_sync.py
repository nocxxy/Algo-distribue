import time
import threading
from Process import Process

def test_broadcast_sync():
    """Test de la fonction broadcastSync"""
    
    print("=== Démarrage du test broadcastSync ===")
    
    # Créer 3 processus
    processes = []
    for i in range(3):
        process = Process(f"NodeBroadcast{i}")
        processes.append(process)
        time.sleep(0.5)  # Délai entre les créations
    
    # Attendre que l'élection soit terminée et que les nœuds soient prêts
    print("=== Attente de la stabilisation du système ===")
    time.sleep(8)
    
    # Afficher l'état du système
    for process in processes:
        state = process.communication.state.value if hasattr(process.communication.state, 'value') else str(process.communication.state)
        print(f"Nœud {process.getId()}: état={state}, leader_id={process.communication.leader_id}")
    
    # Test 1: Le premier nœud fait un broadcastSync
    sender_id = processes[0].getId()
    print(f"\n=== Test 1: broadcastSync depuis le nœud {sender_id} ===")
    
    # Variables pour suivre les résultats
    results = {'sender_done': False, 'receivers_done': [False, False]}
    results_lock = threading.Lock()
    
    def sender_callback(payload):
        with results_lock:
            results['sender_done'] = True
        print(f"🎉 Émetteur {sender_id} terminé - Payload: {payload}")
    
    def receiver_callback(idx):
        def callback(payload):
            with results_lock:
                results['receivers_done'][idx] = True
            print(f"🎉 Récepteur {processes[idx+1].getId()} terminé - Payload reçu: {payload}")
        return callback
    
    # Payload à envoyer
    test_payload = {"message": "Hello from broadcastSync!", "timestamp": time.time()}
    
    # Démarrer les opérations en parallèle
    threads = []
    
    # Thread pour l'émetteur
    def sender_thread():
        processes[0].broadcastSync(test_payload, sender_id, callback=sender_callback)
    
    threads.append(threading.Thread(target=sender_thread))
    
    # Threads pour les récepteurs
    for i in range(1, 3):
        def receiver_thread(idx=i-1):
            processes[i].broadcastSync(None, sender_id, callback=receiver_callback(idx))
        threads.append(threading.Thread(target=receiver_thread))
    
    # Démarrer tous les threads
    for thread in threads:
        thread.start()
    
    # Attendre que tous les threads se terminent
    for thread in threads:
        thread.join(timeout=15)  # Timeout de 15 secondes
    
    # Vérifier les résultats
    time.sleep(1)  # Laisser le temps aux callbacks de s'exécuter
    
    with results_lock:
        success = results['sender_done'] and all(results['receivers_done'])
        
        if success:
            print("✅ Test 1 réussi: broadcastSync fonctionne correctement!")
        else:
            print(f"❌ Test 1 échoué: sender_done={results['sender_done']}, receivers_done={results['receivers_done']}")
    
    # Test 2: Test avec un autre émetteur
    print(f"\n=== Test 2: broadcastSync depuis le nœud {processes[1].getId()} ===")
    
    sender2_id = processes[1].getId()
    test_payload2 = {"message": "Second broadcast test", "number": 42}
    
    results2 = {'all_done': False}
    
    def completion_callback(payload):
        results2['all_done'] = True
        print(f"🎉 Test 2 terminé - Payload: {payload}")
    
    # Test synchrone (bloquant) pour l'émetteur
    def sender2_thread():
        processes[1].broadcastSync(test_payload2, sender2_id, callback=completion_callback)
    
    def receiver2_thread(idx):
        processes[idx].broadcastSync(None, sender2_id, callback=completion_callback)
    
    threads2 = []
    threads2.append(threading.Thread(target=sender2_thread))
    threads2.append(threading.Thread(target=lambda: receiver2_thread(0)))
    threads2.append(threading.Thread(target=lambda: receiver2_thread(2)))
    
    # Démarrer tous les threads
    for thread in threads2:
        thread.start()
    
    # Attendre que tous les threads se terminent
    for thread in threads2:
        thread.join(timeout=15)
    
    time.sleep(1)
    
    if results2['all_done']:
        print("✅ Test 2 réussi!")
    else:
        print("❌ Test 2 échoué")
    
    # Attendre un peu avant d'arrêter
    time.sleep(2)
    
    # Arrêter tous les processus
    print("\n=== Arrêt des processus ===")
    for process in processes:
        process.stop()
    
    # Attendre que tous les processus s'arrêtent
    for process in processes:
        process.waitStopped()
    
    print("Test broadcastSync terminé ✅")

if __name__ == "__main__":
    test_broadcast_sync()