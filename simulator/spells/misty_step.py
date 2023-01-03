from simulator.spells.spell import Spell
import logging
from simulator.actions import BonusAction

logger = logging.getLogger(__name__)
class MistyStep(Spell):
    def __init__(self, coord):
        super().__init__(level=2,
                         spell_range=Spell.Range.FEET_30,
                         target=Spell.Target.SELF,
                         duration=Spell.Duration.INSTANTANEOUS,
                         concentration=False,
                         type=Spell.Type.OTHER,
                         dc=None,
                         dmg_type=None)
        self.action_type = BonusAction.MISTY_STEP
        self.coord = coord
