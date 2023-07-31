import logging

from simulator.effects.effect import EffectType
from simulator.effects.start_of_turn_combatant_auto_effect import StartOfTurnAutoEffect
from simulator.misc import parse_dmg_dice, roll_dice, DamageType

logger = logging.getLogger("Encounterra")

class Digestion(StartOfTurnAutoEffect):

    def get_effect_type(self):
        return EffectType.DIGESTION

    def start_of_turn(self):
        dice = parse_dmg_dice('3d6')
        dmg_dice_sum = roll_dice(dice)
        logger.info(f"{self.target} is being digested for {dmg_dice_sum} dmg")
        self.target.receive_dmg(dmg_dice_sum, DamageType.Acid)
        return True
