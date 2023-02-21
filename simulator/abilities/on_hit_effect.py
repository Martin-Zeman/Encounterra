from abc import ABC, abstractmethod


class OnHit(ABC):

    @abstractmethod
    def hit(self, attacker, attack, target, effect_tracker):
        pass
