from simulator.spells.spell import Spell
from simulator.misc import DamageType
import logging

logger = logging.getLogger(__name__)
class Firebolt(Spell):
    def __init__(self, to_hit, combatant_level, target):
        super().__init__(level=0,
                         casting_time=Spell.CastingTime.ACTION,
                         spell_range=Spell.Range.FEET_120,
                         target=Spell.Target.ONE_CREATURE,
                         duration=Spell.Duration.INSTANTANEOUS,
                         concentration=False,
                         type=Spell.Type.HARMFUL,
                         dc=None,
                         dmg_type=DamageType.Fire)
        self.to_hit = to_hit
        self.target = target
        match combatant_level:
            case lvl if 1 <= lvl <= 4:
                self.dmg_dice = "1d10"
            case lvl if 5 <= lvl <= 10:
                self.dmg_dice = "2d10"
            case lvl if 11 <= lvl <= 16:
                self.dmg_dice = "3d10"
            case lvl if lvl <= 17:
                self.dmg_dice = "4d10"
            case _:
                self.dmg_dice = "1d10"
                logger.error("Incorrect caster level of Firebolt")