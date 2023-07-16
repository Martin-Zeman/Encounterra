from abc import ABC, abstractmethod

class OnHit(ABC):

    @abstractmethod
    def hit(self, attacker, attack, target):
        pass

    @abstractmethod
    def calculate_threat(self, attacker, target, **kwargs):
        pass
