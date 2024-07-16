from cachetools.keys import hashkey

from ..actions.action_types import Action
from ..battle_map import Map, map_position_toggled_cache, map_toggled_cache_with_key
from ..spells.spell import SpellStats
from ..misc import Visibility, Class, get_missing_hp
from ..conditions import Conditions, is_affected_by_any, get_swallower
from ..actions.actoid import Actoid
from ..threat_interfaces import DirectThreat
from ..factory_interfaces import DirectThreatFactory
import logging
import numba_functions as nf
from ..utils.roll_types import ThreatModifierType

logger = logging.getLogger("Encounterra")


class LayOnHandsFactory(DirectThreatFactory):

    range = SpellStats.Range.TOUCH.value
    HP_PER_LEVEL = 5

    def __init__(self, combatant):
        super().__init__()
        self.action_type = Action.LAY_ON_HANDS
        self.combatant = combatant

    def __str__(self):
        """
        Important for FSM building
        """
        return "LayOnHandsFactory"

    def get_ability_name(self):
        return "Lay on Hands"

    def get_eligible_targets(self):
        if get_swallower(self.combatant):
            return []
        ret = [e for e in Map.get().get_non_swallowed_allies(self.combatant) if type(type(e).cls) is not Class.MONSTER or (type(e).cls is not Class.MONSTER.UNDEAD and type(e).cls is not Class.MONSTER.CONSTRUCT)]
        if type(type(self.combatant).cls) is not Class.MONSTER or (type(self.combatant).cls is not Class.MONSTER.UNDEAD and type(self.combatant).cls is not Class.MONSTER.CONSTRUCT):
            ret.append(self.combatant)
        return ret

    def create_all(self, previous_action_in_dag=None):
        targets = self.get_eligible_targets()
        ret = []
        for t in targets:
            missing_hp = get_missing_hp(t)
            max_healable_hp = min(missing_hp, self.combatant.resources[Action.LAY_ON_HANDS].get_resource())

            for hp_amount in range(LayOnHandsFactory.HP_PER_LEVEL, max_healable_hp + LayOnHandsFactory.HP_PER_LEVEL, LayOnHandsFactory.HP_PER_LEVEL):
                # Do not exceed the maximum healable HP
                actual_hp_amount = min(hp_amount, max_healable_hp)
                ret.append(LayOnHands(t, self, actual_hp_amount))
        return ret

    def create(self, target):
        return LayOnHands(target, self, self.combatant.resources[Action.LAY_ON_HANDS].get_resource())

    def calculate_threat_to_target(self, target, **kwargs):
        battle_map = Map.get()
        if get_swallower(target):
            return 0
        if type(type(target).cls) is not Class.MONSTER or (type(target).cls is not Class.MONSTER.UNDEAD and type(target).cls is not Class.MONSTER.CONSTRUCT):
            if battle_map.get_hop_distance_combatants(self.combatant, target) <= LayOnHandsFactory.range:
                missing_hp = get_missing_hp(self.combatant)
                healable_hp = min(missing_hp, kwargs['hp_amount'])
                current_health_percentage = self.combatant.curr_hp / self.combatant.max_hp
                if current_health_percentage <= 0.25:
                    healable_hp * 1.5
                return healable_hp
        return 0

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications.
        This is useful calculating the potential reduction of threat_in caused by abilities of enemies, e.g. advantage on saving throw
        against fireball or bane on attack rolls etc.
        """
        battle_map = Map.get()
        mod_range = modifiers.get(ThreatModifierType.RANGE, 0)
        with battle_map.as_if_dist_delta_from_combatant(self.combatant, target, -mod_range):
            return self.calculate_threat_to_target(target, **kwargs)

    def calculate_max_threat(self):
        return self.combatant.resources[Action.LAY_ON_HANDS].get_resource()


class LayOnHands(Actoid, DirectThreat):
    def __init__(self, target, factory, hp_amount):
        Actoid.__init__(self)
        self.target = target
        self.factory = factory
        self.hp_amount = hp_amount

    def __str__(self):
        return f"Lay on Hands for {self.hp_amount} HP on {self.target}"

    def shorthand_str(self):
        return "Lay on Hands"

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        return self.factory.calculate_threat_to_target(self.target, hp_amount=self.hp_amount)

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        self.calculate_threat_delta.cache_clear()

    @map_toggled_cache_with_key(key=lambda self, modifiers, *args, **kwargs: hashkey(self.factory.name, tuple(modifiers.items()), tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        return self.factory.calculate_threat_to_target_delta(self.target, modifiers, *args, hp_amount=self.hp_amount, **kwargs)

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        if get_swallower(self.factory.combatant):
            return None
        battle_map = Map.get()
        curr_coord = tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])
        if not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            free_coords_in_range = nf.get_free_coords_in_hop_range(
                battle_map.grid,
                battle_map.get_combatant_position(self.target).get(),
                distances,
                inflate_to_dist=self.factory.combatant.size.value,
                rng=LayOnHandsFactory.range, combatant_id=self.factory.combatant.id)
            return [coord for coord in free_coords_in_range if battle_map.visibility_dict_for_all_coords[coord][self.target] is not Visibility.NONE]
        elif battle_map.get_hop_distance_combatants(self.factory.combatant, self.target) <= LayOnHandsFactory.range and \
                battle_map.visibility_dict_for_all_coords[curr_coord][self.target] is not Visibility.NONE:
            return [curr_coord]
        return None

