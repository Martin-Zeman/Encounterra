import logging

from ..effects.effect import EffectType
from ..effects.start_of_turn_combatant_auto_effect import StartOfTurnAutoEffect
from ..misc import parse_dmg_dice, roll_dice, DamageType
from ..battle_map import Map

logger = logging.getLogger("Encounterra")


class DigestionEffect(StartOfTurnAutoEffect):

    def get_effect_type(self):
        return EffectType.DIGESTION

    def start_of_turn(self):
        dice = parse_dmg_dice('3d6')
        dmg_dice_sum = roll_dice(dice)
        logger.info(f"{self.combatants[0]} is being digested for {dmg_dice_sum} dmg")
        self.combatants[0].receive_dmg(dmg_dice_sum, DamageType.Acid)
        Map.get().remove_combatant_if_dead(self.combatants[0])
        return True
