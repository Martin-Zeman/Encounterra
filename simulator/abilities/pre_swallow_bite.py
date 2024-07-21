import math

from ..actions.actoid import FactoryFlags
from ..actions.melee_attack import MeleeAttackFactory, MeleeAttack
from ..battle_map import Map
from ..conditions import Conditions, is_affected_by_any, get_grappled
import logging
import numba_functions as nf

from ..resources import ResourceRefreshType, Uses

logger = logging.getLogger("Encounterra")


class PreSwallowBiteFactory(MeleeAttackFactory):

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range=1, ammo=Uses(math.inf, ResourceRefreshType.NEVER), on_hit=None, extra_dmg=None, **kwargs):
        super().__init__(name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range, ammo, on_hit, extra_dmg)
        self.flags |= FactoryFlags.IS_MELEE

    def get_ability_name(self):
        return "Bite with grapple"

    def create(self, target):
        grappled_target = get_grappled(self.combatant)
        if grappled_target is None or (grappled_target is target and target.is_alive()):
            return PreSwallowBite(target, self)
        return None

    def create_all(self, previous_action_in_dag=None):
        grappled_target = get_grappled(self.combatant)
        if grappled_target is not None and grappled_target.is_alive():
            return [PreSwallowBite(grappled_target, self)]
        targets = self.get_eligible_targets()
        return [PreSwallowBite(t, self) for t in targets]


class PreSwallowBite(MeleeAttack):

    def shorthand_str(self):
        return "Bite"


    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        if not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            return nf.get_free_coords_in_hop_range(
                battle_map.grid,
                battle_map.get_combatant_position(self.target).get(),
                distances,
                self.factory.combatant.size.value,
                self.factory.range,
                self.factory.combatant.id)
        elif battle_map.are_in_hop_range(self.factory.combatant, self.target, self.factory.range):
            return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]
        return None
