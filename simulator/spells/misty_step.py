from functools import cache

from cachetools import cached
from cachetools.keys import hashkey

from ..battle_map import Map, map_toggled_cache_with_key
from ..spells.spell import SpellStats
import logging
from ..actions.action_types import BonusAction
from ..actions.actoid import Actoid, ActoidFlags, FactoryFlags
from ..threat_interfaces import Threat
from ..factory_interfaces import Factory

logger = logging.getLogger("Encounterra")

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


    def get_ability_name(self):
        return "Misty Step"


    def __str__(self):
        """
        Important for FSM building
        """
        return "MistyStepFactory"

    def get_eligible_targets(self):
        swallower = self.combatant.get_swallower()
        if swallower:
            return []  # Can't see while being swallowed
        return [(0, 0)]
        # battle_map = Map.get()
        # # TODO Add visibility
        # return battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.combatant),
        #                                                      rng=MistyStepFactory.range)

    def create_all(self, previous_action_in_dag=None):
        targets = self.get_eligible_targets()
        return [MistyStep(t, self) for t in targets]

    def create(self, coord):
        return MistyStep(coord, self)



class MistyStep(Actoid, Threat):

    def __init__(self, coord, factory):
        Actoid.__init__(self, ActoidFlags.IS_SPELL)
        self.coord = coord
        self.factory = factory

    def __str__(self):
        return f"Misty Step to {self.coord[0]}, {self.coord[1]}"

    def shorthand_str(self):
        return "Misty Step"

    def calculate_threat(self, **kwargs):
        return 0  # Misty Step is handled differently

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        if self.factory.combatant.get_swallower():
            return None
        battle_map = Map.get()
        # if self.factory.combatant.movement > 0:
        #     return battle_map.get_all_accessible_coords(shortest_paths, self.factory.combatant)
        return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]
