from simulator.spells.spell import Spell
from simulator.misc import SavingThrow, DamageType
import numpy as np

class Fireball(Spell):
    def __init__(self, coord, dc, level=3, has_spell_sculpting=False):
        level = min(max(level, 3), 9)
        super().__init__(level=level,
                         casting_time=Spell.CastingTime.ACTION,
                         range=Spell.Range.FEET_150,
                         target=Spell.Target.RADIUS_20,
                         duration=Spell.Duration.INSTANTANEOUS,
                         concentration=False,
                         type=Spell.Type.HARMFUL,
                         dc=dc,
                         dmg_type=DamageType.Fire)
        self.saving_throw = SavingThrow.DEX
        self.coord = coord
        self.dmg = "8d6"
        self.additional_upcast_dmg = "1d6"