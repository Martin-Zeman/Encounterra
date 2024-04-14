from abc import ABC, abstractmethod

class OnHit(ABC):

    @abstractmethod
    def hit(self, attacker, attack, target, multiplier, dmg_so_far):
        pass

    @abstractmethod
    def calculate_threat(self, attacker, target, **kwargs):
        pass

    def name(self):
        return self.name
