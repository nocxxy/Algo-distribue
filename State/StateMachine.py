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
    
    @abstractmethod
    def on_timeout(self):
        """Actions à effectuer lors d'un timeout"""
        pass