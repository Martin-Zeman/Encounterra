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

    def deactivate(self):
        pass

    def deactivate_for_combatant(self, combatant):
        pass

    def start_of_turn_for_combatant(self, combatant):
        assert self.initiator is combatant, "The initiator of the regeneration effect is not the target combatant!"
        if combatant.is_alive():  # TODO do I need this?
            if self.suppression_dmg_type not in combatant.dmg_types_took_last_round:
                logger.info(f"{combatant} regenerates {self.hp} HP")
                combatant.heal(self.hp)
            else:
                logger.info(f"{combatant}'s regeneration was suppressed by taking {self.suppression_dmg_type.name}")
            return True
        return False
