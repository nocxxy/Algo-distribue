from threading import Lock, Thread
from time import sleep
from Communication import Communication

class Process(Thread):

    def __init__(self, name):
        Thread.__init__(self)

        self.myProcessName = name
        self.myId = None
        self.setName("MainThread-" + name)

        # Communication
        self.communication = Communication()

        #   Contrôle du thread
        self.alive = True
        self.start()

    def run(self):
        """Boucle principale du processus"""
        # Initialisation de la communication
        self.communication.init()
        
        # Récupération de l'ID attribué
        self.myId = self.communication.get_rank()
        print(f"[Node {self.myId}] 🚀 Démarrage")

        loop = 0
        while self.alive:
            if self.communication.hasLetterMessage():
                message = self.communication.retrieveLetterMessage()
                print(f"[Node {self.myId}] 📩 Reçu: {message}")


            # Log périodique
            if loop % 100 == 0:  # Toutes les secondes (10ms * 100)
                self.communication.requestToken()
                sleep(0.1)  # Simuler une section critique
                self.communication.releaseToken()
                print(f"[Node {self.myId}] Loop {loop}")
            
            sleep(0.01)  # 10ms
            loop += 1
        
        print(f"[Node {self.myId}] 🛑 Arrêté")

    def stop(self):
        self.alive = False
        self.communication.stop()

    def waitStopped(self):
        self.join()

    def getId(self):
        return self.communication.get_rank()
    
    def synchronize(self, callback=None):
        """Déclenche la synchronisation"""
        return self.communication.synchronize(callback)
    
    def broadcastSync(self, payload, from_id, callback=None):
        """
        Broadcast synchrone:
        - Si ce processus a l'ID 'from_id', il envoie le message et attend les ACKs
        - Sinon, il attend de recevoir le message de 'from_id'
        """
        return self.communication.broadcastSync(payload, from_id, callback)
    
    def sendToSync(self, payload, dest_id, callback=None):
        """
        Envoie un message de manière synchrone à un destinataire spécifique.
        Bloque jusqu'à ce que le destinataire ait reçu le message.
        """
        return self.communication.sendToSync(payload, dest_id, callback)
    
    def receiveFromSync(self, from_id, callback=None):
        """
        Attend de recevoir un message synchrone d'un expéditeur spécifique.
        Bloque jusqu'à ce que le message arrive.
        """
        return self.communication.receiveFromSync(from_id, callback)

    

