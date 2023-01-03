from simulator.spells.spell import Spell
from simulator.misc import SavingThrow, DamageType
from simulator.actions import Action


class Fireball(Spell):
    def __init__(self, coord, dc, level=3, has_spell_sculpting=False):
        level = min(max(level, 3), 9)
        super().__init__(level=level,
                         spell_range=Spell.Range.FEET_150,
                         target=Spell.Target.RADIUS_20,
                         duration=Spell.Duration.INSTANTANEOUS,
                         concentration=False,
                         type=Spell.Type.HARMFUL,
                         dc=dc,
                         dmg_type=DamageType.Fire)
        self.action_type = Action.FIREBALL
        self.saving_throw = SavingThrow.DEX
        self.coord = coord
        self.dmg_dice = "8d6"
        self.additional_upcast_dmg = "1d6"
