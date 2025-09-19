from abc import ABC, abstractmethod

class StateMachine(ABC):
    """Interface pour les machines à états"""
    
    def __init__(self, communication):
        self.communication = communication
    
    @abstractmethod
    def enter_state(self):
        """Actions à effectuer lors de l'entrée dans l'état"""
        pass
    
    @abstractmethod
    def handle_message(self, message):
        """Traite un message reçu dans cet état"""
        pass
    
    def cleanup(self):
        """Nettoie les ressources avant de quitter l'état (timers, etc.)"""
        # Implémentation par défaut vide, à surcharger si nécessaire
        pass
    
    @abstractmethod
    def on_timeout(self):
        """Actions à effectuer lors d'un timeout"""
        pass
        """Actions à effectuer lors d'un timeout"""
        pass