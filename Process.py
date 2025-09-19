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

    

