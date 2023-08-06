from functools import cache
from simulator.battle_map import Map
from simulator.spells.spell import SpellStats
import logging
from simulator.actions.action_types import BonusAction
from simulator.actions.actoid import Actoid, ActoidFlags, FactoryFlags
from simulator.threat_interfaces import Factory, Threat

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

    def create_all(self):
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

    def get_eligible_coords(self, distances, shortest_paths):
        if self.factory.combatant.get_swallower():
            return None
        battle_map = Map.get()
        if self.factory.combatant.movement > 0:
            return battle_map.get_all_accessible_coords(shortest_paths, self.factory.combatant)
        return set([tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])])
