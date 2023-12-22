import logging

from ..effects.combatant_effect import CombatantEffect
from ..effects.effect import EffectType

logger = logging.getLogger("Encounterra")


class RegenerationEffect(CombatantEffect):
    def __init__(self, combatant, hp, suppression_dmg_type):
        CombatantEffect.__init__(self, combatant, combatants=[combatant])
        self.hp = hp
        self.suppression_dmg_type = suppression_dmg_type

    def get_effect_type(self):
        return EffectType.REGENERATION

    def activate(self, **kwargs):
        pass

    def deactivate(self, **kwargs):
        return False

    def start_of_turn(self):
        if self.initiator.is_alive():
            if self.suppression_dmg_type not in self.initiator.dmg_types_took_last_round:
                logger.info(f"{self.initiator} regenerates {self.hp} HP")
                self.initiator.heal(self.hp)
            else:
                logger.info(f"{self.initiator}'s regeneration was suppressed by taking {self.suppression_dmg_type.name}")
            return True
