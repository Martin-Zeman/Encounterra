from simulator.spells.spell import SpellStats
from simulator.action_types import Reaction
import logging
from simulator.actoid import Actoid

logger = logging.getLogger(__name__)


class Shield(Actoid):

    level = 1
    spell_range = SpellStats.Range.SELF
    target = SpellStats.Target.SELF
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = False
    type = SpellStats.Type.BUFF
    dc = None
    dmg_type = None

    def __init__(self):
        super().__init__(Actoid.Type.IS_SPELL)
        self.action_type = Reaction.SHIELD


    @staticmethod
    def calculate_threat_approx(combatant, battle_map, *args, **kwargs):
        return 0

    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        return 0
