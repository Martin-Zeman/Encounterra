from functools import cache

from simulator.combatant_coords import CombatantCoords
from simulator.spells.spell import SpellStats
import logging
from simulator.actions.action_types import BonusAction
from simulator.actions.actoid import Actoid, ActoidFlags, FactoryFlags
from simulator.threat_interfaces import ThreatModifier, DirectThreatFactory, Factory

logger = logging.getLogger("EncounTroll")

class MistyStepFactory(Factory):
    level = 2
    range = SpellStats.Range.FEET_30.value
    target = SpellStats.Target.SELF
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = False
    type = SpellStats.Type.OTHER
    dc = None
    dmg_type = None

    def __init__(self, caster):
        super().__init__()
        self.flags |= FactoryFlags.TARGETS_COORDS
        self.action_type = BonusAction.MISTY_STEP
        self.combatant = caster


    def __str__(self):
        """
        Important for FSM building
        """
        return "MistyStepFactory"

    def get_eligible_targets(self, battle_map):
        return battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.combatant),
                                                             rng=MistyStepFactory.range)

    def create_all(self, battle_map):
        targets = self.get_eligible_targets(battle_map)
        return [MistyStep(t, self) for t in targets]

    def create(self, coord):
        return MistyStep(coord, self)



class MistyStep(Actoid, ThreatModifier):

    def __init__(self, coord, factory):
        Actoid.__init__(self, ActoidFlags.IS_SPELL)
        self.coord = coord
        self.factory = factory

    def __str__(self):
        return f"Misty Step to {self.coord[0]}, {self.coord[1]}"

    def shorthand_str(self):
        return "Misty Step"


    def clear_cache(self):
        self.calculate_threat.cache_clear()

    @cache
    def calculate_threat(self, battle_map, *args, **kwargs):
        return 0  # Misty Step is handled differently

    def get_eligible_coords(self, battle_map, distances, shortest_paths):
        return battle_map.get_all_accessible_coords(shortest_paths, self.factory.combatant)

    def is_current_coord_eligible(self, battle_map):
        return True