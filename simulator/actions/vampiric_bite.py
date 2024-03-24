import math

from .grapple_attack import GrappleAttack
from ..actions.melee_attack import MeleeAttackFactory, MeleeAttack
from ..battle_map import Map, map_position_toggled_cache
from ..misc import Size
from ..conditions import Conditions, is_affected_by_any, is_affected_by, get_swallower, get_grappler
import logging

from ..resources import Uses, ResourceRefreshType

logger = logging.getLogger("Encounterra")


class VampiricBiteFactory(MeleeAttackFactory):

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range=1, ammo=Uses(math.inf, ResourceRefreshType.NEVER), on_hit=[]):
        super().__init__(name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range, ammo, on_hit, [])

    def get_ability_name(self):
        return "Vampiric Bite"

    def get_eligible_targets(self):
        swallower = get_swallower(self.combatant)
        if swallower:
            return []
        return [e for e in Map.get().get_non_swallowed_enemies(self.combatant) if
                (is_affected_by_any(e, Conditions.INCAPACITATED, Conditions.RESTRAINED)
                 or get_grappler(e) is self.combatant)]

    def create(self, target):
        if get_grappler(target) is self.combatant or is_affected_by_any(target, Conditions.INCAPACITATED, Conditions.RESTRAINED):
            return VampiricBite(target, self)
        return []

    def create_all(self, previous_action_in_dag=None):
        if previous_action_in_dag and isinstance(previous_action_in_dag, GrappleAttack):
            return [VampiricBite(previous_action_in_dag.target, self)]
        targets = self.get_eligible_targets()
        return [VampiricBite(t, self) for t in targets]


class VampiricBite(MeleeAttack):

    def shorthand_str(self):
        return "Vampiric Bite"

    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        swallower = get_swallower(self.factory.combatant)
        if swallower:
            return None
        if not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            return battle_map.get_free_coords_in_hop_range(battle_map.get_combatant_position(self.target),
                                                           distances,
                                                           inflate_to_dist=self.factory.combatant.size.value,
                                                           rng=self.factory.range,
                                                           combatant=self.factory.combatant)
        elif battle_map.are_in_hop_range(self.factory.combatant, self.target, self.factory.range):
            return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        """
        The conditional nature of this follow-up attack is modeled by moving all the entire threat contribution to the
        preceding threat modifier grapple attack. This attack only generates threat if the target is already affected
        by the necessary pre-conditions.
        """
        if get_grappler(self.target) is self.factory.combatant or is_affected_by_any(self.target, Conditions.INCAPACITATED, Conditions.RESTRAINED):
            return self.factory.calculate_threat_to_target(self.target, **kwargs)
        return 0  # In this case, the threat is fully captured by the preceding grapple
