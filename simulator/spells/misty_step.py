from simulator.spells.spell import SpellStats
import logging
from simulator.action_types import BonusAction
from simulator.actoid import Actoid
from simulator.threat_calculator import DirectThreat

logger = logging.getLogger(__name__)

class MistyStepFactory:

    def __init__(self, coord, caster):
        self.action_type = BonusAction.MISTY_STEP
        self.coord = coord
        self.caster = caster

    def find_best_args(self, combatant, battle_map):
        return battle_map.get_free_coords_away_from_enemies(combatant, MistyStep.spell_range.value)

    def create_best(self, combatant, battle_map, **kwargs):
        return MistyStep(self.find_best_args(combatant, battle_map), self)


class MistyStep(Actoid, DirectThreat):

    level = 2
    spell_range = SpellStats.Range.FEET_30
    target = SpellStats.Target.SELF
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = False
    type = SpellStats.Type.OTHER
    dc = None
    dmg_type = None

    def __init__(self, coord, factory):
        super().__init__(Actoid.Type.IS_SPELL)
        self.coord = coord
        self.factory = factory

    @staticmethod
    def calculate_threat_approx(combatant, battle_map, *args, **kwargs):
        # This may make sense as zero
        return 0

    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        # TODO Add up all potential dmg from enemies that would normally be withing their movement range
        # this can be arbitrated between other bonus action abilities
        return 0
