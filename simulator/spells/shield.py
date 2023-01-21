from simulator.spells.spell import SpellStats
from simulator.action_types import Reaction
import logging
from simulator.actoid import Actoid
from simulator.threat_calculator import ReactionToThreat

logger = logging.getLogger(__name__)

class ShieldFactory:

    def __init__(self):
        super().__init__(Actoid.Type.IS_SPELL)
        self.action_type = Reaction.SHIELD



class Shield(Actoid, ReactionToThreat):

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


    def calculate_threat_mod(self, combatant, battle_map, incoming_action, actor, *args, **kwargs):
        return 0
