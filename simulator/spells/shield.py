from simulator.spells.spell import SpellStats
from simulator.action_types import Reaction
import logging
from simulator.actions.actoid import Actoid
from simulator.threat_calculator import ReactionToThreat, FactoryThreat

logger = logging.getLogger(__name__)

class ShieldFactory(FactoryThreat):

    def __init__(self, caster):
        super().__init__(Actoid.Type.IS_SPELL)
        self.action_type = Reaction.SHIELD
        self.caster = caster

    def calculate_threat_approx_mod(self, battle_map, modified_stats, *args, **kwargs):
        return 0  # no need

    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        return 0

    def calculate_threat_to_target_mod(self, battle_map, target, modified_stats, *args, **kwargs):
        return 0


class Shield(Actoid, ReactionToThreat):

    level = 1
    spell_range = SpellStats.Range.SELF
    target = SpellStats.Target.SELF
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = False
    type = SpellStats.Type.BUFF
    dc = None
    dmg_type = None

    def __init__(self, factory):
        super().__init__(Actoid.Type.IS_SPELL)
        self.action_type = Reaction.SHIELD
        self.factory = factory


    def calculate_threat_mod(self, combatant, battle_map, incoming_action, actor, *args, **kwargs):
        return 0 # TODO Consider removing this from ReactionToThreat altogether
