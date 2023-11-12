import math
from ..actions.melee_attack import MeleeAttackFactory, MeleeAttack
from ..battle_map import Map, map_position_toggled_cache
from ..misc import Size, Conditions
import logging

logger = logging.getLogger("Encounterra")


class VampiricBiteFactory(MeleeAttackFactory):

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range=1, ammo=math.inf, on_hit=None):
        super().__init__(name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range, ammo, on_hit, [])

    def get_ability_name(self):
        return "Vampiric Bite"

    def create(self, target):
        if self.combatant.constricted_target is target and target.is_alive() and target.size.value <= Size.MEDIUM.value:
            return VampiricBite(target, self)
        return None

    def create_all(self):
        # if self.combatant.constricted_target is not None and self.combatant.constricted_target.size <= Size.MEDIUM:
        if self.combatant.constricted_target.is_alive():
            return [VampiricBite(self.combatant.constricted_target, self)]
        return None


class VampiricBite(MeleeAttack):

    def shorthand_str(self):
        return "Vampiric Bite"

    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        swallower = self.factory.combatant.get_swallower()
        if swallower:
            return None
        if not self.factory.combatant.is_affected_by_any(Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            return battle_map.get_free_coords_in_hop_range(battle_map.get_combatant_position(self.target),
                                                           distances,
                                                           inflate_to_size=self.factory.combatant.size,
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
        if self.target.get_grappler() is self.factory.combatant or self.target.is_affected_by_any(Conditions.INCAPACITATED, Conditions.RESTRAINED):
            return self.factory.calculate_threat_to_target(self.target, **kwargs)
        return 0  # In this case, the threat is fully captured by the preceding grapple
