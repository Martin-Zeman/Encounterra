from itertools import combinations

from cachetools.keys import hashkey

from ..actions.action_types import BonusAction
from ..battle_map import Map, map_position_toggled_cache, map_toggled_cache_with_key
from ..spells.spell import SpellStats
from ..misc import Visibility, Class, get_missing_hp
from ..conditions import Conditions, is_affected_by_any, get_swallower
from ..actions.actoid import Actoid, ActoidFlags
from ..threat_interfaces import DirectThreat
from ..factory_interfaces import DirectThreatFactory
import logging
import numba_functions as nf
from ..utils.roll_types import ThreatModifierType

logger = logging.getLogger("Encounterra")


class TwinnedHealingWordFactory(DirectThreatFactory):
    level = 1
    range = SpellStats.Range.FEET_60.value
    target = SpellStats.Target.ONE_CREATURE
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = False
    type = SpellStats.Type.OTHER
    dc = None

    def __init__(self, to_hit, mod, caster, resource):
        super().__init__()
        self.to_hit = to_hit
        self.mod = mod
        self.action_type = BonusAction.HEALING_WORD
        self.heal_dice = (1, 4)
        self.combatant = caster
        self.resource = resource

    def __str__(self):
        """
        Important for FSM building
        """
        return "TwinnedHealingWordFactory"

    def get_ability_name(self):
        return "Twinned Healing Word"

    def get_eligible_targets(self):
        if get_swallower(self.combatant):
            return []
        ret = [e for e in Map.get().get_non_swallowed_allies(self.combatant) if type(type(e).cls) is not Class.MONSTER or (type(e).cls is not Class.MONSTER.UNDEAD and type(e).cls is not Class.MONSTER.CONSTRUCT)]
        if type(type(self.combatant).cls) is not Class.MONSTER or (type(self.combatant).cls is not Class.MONSTER.UNDEAD and type(self.combatant).cls is not Class.MONSTER.CONSTRUCT):
            ret.append(self.combatant)
        if len(ret) < 2:
            return []  # Let's not waste a twinned version on this
        return combinations(ret, 2)

    def create_all(self, previous_action_in_dag=None):
        targets = self.get_eligible_targets()
        return [TwinnedHealingWord(t, self) for t in targets]

    def create(self, targets):
        return TwinnedHealingWord(targets, self)

    def calculate_threat_to_target(self, target, **kwargs):
        battle_map = Map.get()
        if get_swallower(target):
            return 0
        if battle_map.get_cartesian_distance_combatants(self.combatant, target) <= TwinnedHealingWordFactory.range:
            missing_hp = get_missing_hp(self.combatant)
            return min(missing_hp, nf.avg_roll(self.heal_dice) + self.mod)
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
            return self.calculate_threat_to_target(target)

    def calculate_max_threat(self):
        return nf.avg_roll(self.heal_dice) + self.mod


class TwinnedHealingWord(Actoid, DirectThreat):
    def __init__(self, targets, factory):
        Actoid.__init__(self, ActoidFlags.IS_SPELL)
        self.targets = targets
        self.factory = factory

    def __str__(self):
        return f"Twinned Healing Word on {self.targets[0]} and {self.targets[1]}"

    def shorthand_str(self):
        return "Twinned Healing Word"

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        ret = self.factory.calculate_threat_to_target(self.targets[0])
        if self.targets[1] is not None:
            ret += self.factory.calculate_threat_to_target(self.targets[1])
        return ret

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        self.calculate_threat_delta.cache_clear()

    @map_toggled_cache_with_key(key=lambda self, modifiers, *args, **kwargs: hashkey(self.factory.name, tuple(modifiers.items()), tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        ret = self.factory.calculate_threat_to_target_delta(self.targets[0], modifiers, *args, **kwargs)
        if self.targets[1] is not None:
            ret += self.factory.calculate_threat_to_target_delta(self.targets[1], modifiers, *args, **kwargs)
        return ret

    def get_eligible_coords(self, distances, shortest_paths):
        if get_swallower(self.factory.combatant):
            return None
        battle_map = Map.get()
        curr_coord = tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])
        if not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            coords_for_fist = set(nf.get_free_coords_in_cartesian_range(
                battle_map.grid,
                battle_map.get_combatant_position(self.targets[0]).get(),
                distances,
                self.factory.combatant.size.value,
                TwinnedHealingWordFactory.range,
                self.factory.combatant.id))
            coords_for_second = set(nf.get_free_coords_in_cartesian_range(
                battle_map.grid,
                battle_map.get_combatant_position(self.targets[1]).get(),
                distances,
                self.factory.combatant.size.value,
                TwinnedHealingWordFactory.range,
                self.factory.combatant.id))
            free_coords_in_range = coords_for_fist.intersection(coords_for_second)

            return [coord for coord in free_coords_in_range if battle_map.visibility_dict_for_all_coords[coord][self.targets[0]] is not Visibility.NONE
                    and battle_map.visibility_dict_for_all_coords[coord][self.targets[1]] is not Visibility.NONE]
        elif battle_map.get_cartesian_distance_combatants(self.factory.combatant, self.targets[0]) <= TwinnedHealingWordFactory.range \
            and battle_map.get_cartesian_distance_combatants(self.factory.combatant, self.targets[1]) <= TwinnedHealingWordFactory.range \
                and battle_map.visibility_dict_for_all_coords[curr_coord][self.targets[0]] is not Visibility.NONE \
                and battle_map.visibility_dict_for_all_coords[curr_coord][self.targets[1]] is not Visibility.NONE:
            return [curr_coord]
        return None
