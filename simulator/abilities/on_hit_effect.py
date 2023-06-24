from abc import ABC, abstractmethod

class OnHit(ABC):

    @abstractmethod
    def hit(self, attacker, attack, target, effect_tracker):
        pass

    @abstractmethod
    def calculate_threat(self, attacker, target, battle_map, *args, **kwargs):
        pass
