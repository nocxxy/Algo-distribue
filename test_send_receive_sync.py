import time
import threading
from Process import Process

def test_send_receive_sync():
    """Test des communications synchrones point-à-point"""
    
    print("=== Test sendToSync et receiveFromSync ===")
    print("Ce test vérifie la communication synchrone point-à-point:")
    print("- sendToSync: envoie un message et attend que le destinataire l'ait reçu")
    print("- receiveFromSync: attend de recevoir un message d'un expéditeur spécifique")
    
    # Créer 3 processus
    processes = []
    for i in range(3):
        process = Process(f"SyncTest{i}")
        processes.append(process)
        time.sleep(0.3)
    
    # Attendre la stabilisation
    print("\n⏳ Attente de la stabilisation du système...")
    time.sleep(6)
    
    # Identifier les nœuds
    node_ids = [p.getId() for p in processes]
    print(f"📋 Nœuds créés: {node_ids}")
    
    # Test 1: Nœud 0 envoie à Nœud 1
    sender_id = node_ids[0]
    receiver_id = node_ids[1]
    observer_id = node_ids[2]
    
    print(f"\n=== Test 1: {sender_id} → {receiver_id} ===")
    
    message1 = {
        "type": "test1",
        "content": "Message de test sendToSync/receiveFromSync",
        "timestamp": time.time(),
        "from": sender_id,
        "to": receiver_id
    }
    
    results = []
    results_lock = threading.Lock()
    
    def sender_task():
        try:
            print(f"📤 Nœud {sender_id} démarre sendToSync vers {receiver_id}")
            success = processes[0].sendToSync(message1, receiver_id)
            
            with results_lock:
                if success:
                    results.append(f"✅ Nœud {sender_id} a envoyé avec succès")
                    print(f"✅ Nœud {sender_id} a envoyé avec succès")
                else:
                    results.append(f"❌ Nœud {sender_id} échec de l'envoi")
                    print(f"❌ Nœud {sender_id} échec de l'envoi")
        except Exception as e:
            with results_lock:
                results.append(f"❌ Nœud {sender_id} erreur: {e}")
                print(f"❌ Nœud {sender_id} erreur: {e}")
    
    def receiver_task():
        try:
            print(f"📥 Nœud {receiver_id} démarre receiveFromSync de {sender_id}")
            payload = processes[1].receiveFromSync(sender_id)
            
            with results_lock:
                if payload:
                    results.append(f"✅ Nœud {receiver_id} a reçu: {payload}")
                    print(f"✅ Nœud {receiver_id} a reçu: {payload}")
                else:
                    results.append(f"❌ Nœud {receiver_id} n'a rien reçu")
                    print(f"❌ Nœud {receiver_id} n'a rien reçu")
        except Exception as e:
            with results_lock:
                results.append(f"❌ Nœud {receiver_id} erreur: {e}")
                print(f"❌ Nœud {receiver_id} erreur: {e}")
    
    # Démarrer sender et receiver en parallèle
    sender_thread = threading.Thread(target=sender_task)
    receiver_thread = threading.Thread(target=receiver_task)
    
    # Démarrer d'abord le receiver
    receiver_thread.start()
    time.sleep(0.5)  # Petit délai pour s'assurer que le receiver est prêt
    sender_thread.start()
    
    # Attendre les résultats
    sender_thread.join(timeout=20)
    receiver_thread.join(timeout=20)
    
    print(f"\n📊 Résultats Test 1 ({len(results)}/2):")
    for result in results:
        print(f"  {result}")
    
    # Test 2: Communication inverse
    print(f"\n=== Test 2: {receiver_id} → {sender_id} ===")
    
    message2 = {
        "type": "test2",
        "content": "Message retour",
        "timestamp": time.time(),
        "from": receiver_id,
        "to": sender_id
    }
    
    results2 = []
    
    def sender_task2():
        try:
            print(f"📤 Nœud {receiver_id} démarre sendToSync vers {sender_id}")
            success = processes[1].sendToSync(message2, sender_id)
            
            with results_lock:
                if success:
                    results2.append(f"✅ Nœud {receiver_id} a envoyé avec succès")
                    print(f"✅ Nœud {receiver_id} a envoyé avec succès")
                else:
                    results2.append(f"❌ Nœud {receiver_id} échec de l'envoi")
                    print(f"❌ Nœud {receiver_id} échec de l'envoi")
        except Exception as e:
            with results_lock:
                results2.append(f"❌ Nœud {receiver_id} erreur: {e}")
                print(f"❌ Nœud {receiver_id} erreur: {e}")
    
    def receiver_task2():
        try:
            print(f"📥 Nœud {sender_id} démarre receiveFromSync de {receiver_id}")
            payload = processes[0].receiveFromSync(receiver_id)
            
            with results_lock:
                if payload:
                    results2.append(f"✅ Nœud {sender_id} a reçu: {payload}")
                    print(f"✅ Nœud {sender_id} a reçu: {payload}")
                else:
                    results2.append(f"❌ Nœud {sender_id} n'a rien reçu")
                    print(f"❌ Nœud {sender_id} n'a rien reçu")
        except Exception as e:
            with results_lock:
                results2.append(f"❌ Nœud {sender_id} erreur: {e}")
                print(f"❌ Nœud {sender_id} erreur: {e}")
    
    # Démarrer la communication inverse
    sender_thread2 = threading.Thread(target=sender_task2)
    receiver_thread2 = threading.Thread(target=receiver_task2)
    
    receiver_thread2.start()
    time.sleep(0.5)
    sender_thread2.start()
    
    sender_thread2.join(timeout=20)
    receiver_thread2.join(timeout=20)
    
    print(f"\n📊 Résultats Test 2 ({len(results2)}/2):")
    for result in results2:
        print(f"  {result}")
    
    # Résumé final
    total_success = len(results) + len(results2)
    print(f"\n🎯 Résumé final: {total_success}/4 opérations réussies")
    
    if total_success == 4:
        print("🎉 Tous les tests sendToSync/receiveFromSync ont réussi!")
    elif total_success >= 2:
        print("⚠️  Tests partiellement réussis")
    else:
        print("❌ Échec des tests")
    
    # Nettoyage
    print("\n🛑 Arrêt des processus...")
    for process in processes:
        process.stop()
    
    for process in processes:
        process.waitStopped()
    
    print("✅ Test terminé!")

if __name__ == "__main__":
    test_send_receive_sync()
