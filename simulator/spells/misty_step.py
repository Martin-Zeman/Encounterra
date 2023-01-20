from simulator.spells.spell import SpellStats
import logging
from simulator.action_types import BonusAction
from simulator.actoid import Actoid

logger = logging.getLogger(__name__)
class MistyStep(Actoid):

    level = 2
    spell_range = SpellStats.Range.FEET_30
    target = SpellStats.Target.SELF
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = False
    type = SpellStats.Type.OTHER
    dc = None
    dmg_type = None
    def __init__(self, coord):
        super().__init__(Actoid.Type.IS_SPELL)
        self.action_type = BonusAction.MISTY_STEP
        self.coord = coord

    @staticmethod
    def calculate_threat_approx(combatant, battle_map, *args, **kwargs):
        return 0

    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        return 0
