import logging

from ..effects.effect import EffectType
from ..effects.start_of_turn_combatant_auto_effect import StartOfTurnAutoEffect
from ..misc import parse_dmg_dice, roll_dice, DamageType
from ..battle_map import Map

logger = logging.getLogger("Encounterra")


class DigestionEffect(StartOfTurnAutoEffect):

    def get_effect_type(self):
        return EffectType.DIGESTION

    def start_of_turn_for_combatant(self, combatant):
        dice = parse_dmg_dice('3d6')
        dmg_dice_sum = roll_dice(dice)
        logger.info(f"{combatant} is being digested for {dmg_dice_sum} dmg")
        combatant.receive_dmg(dmg_dice_sum, DamageType.Acid)
        if not combatant.is_alive():
            Map.get().remove_combatant_if_dead(combatant)
            self.initiator.swallowed_target = None
            return False
        return True

    def deactivate_for_combatant(self, combatant):
        pass  # The only way this can be deactivated for the combatant is if the combatant's dead, no need to do anything else
