from cachetools.keys import hashkey

from ..battle_map import Map, map_position_toggled_cache, map_toggled_cache_with_key, \
    _get_free_coords_in_cartesian_range
from ..spells.spell import SpellStats
from ..misc import avg_roll, Class, get_missing_hp
from ..conditions import Conditions, is_affected_by_any, get_swallower
from ..actions.actoid import Actoid, ActoidFlags
from ..threat_interfaces import DirectThreat
from ..factory_interfaces import DirectThreatFactory
import logging
from ..utils.roll_types import ThreatModifierType

logger = logging.getLogger("Encounterra")


class CureWoundsFactory(DirectThreatFactory):
    level = 1
    range = SpellStats.Range.TOUCH.value
    target = SpellStats.Target.ONE_CREATURE
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = False
    type = SpellStats.Type.OTHER
    dc = None

    def __init__(self, action_type, caster, resource, mod):
        super().__init__()
        self.mod = mod
        self.action_type = action_type  # CURE_WOUNDS or QUICKENED_CURE_WOUNDS
        self.heal_dice = (1, 8)
        self.combatant = caster
        self.resource = resource

    def __str__(self):
        """
        Important for FSM building
        """
        return "CureWoundsFactory"

    def get_ability_name(self):
        return "Cure Wounds"

    def get_twinned_kwargs(self):
        return {'mod': self.mod, 'caster': self.combatant, 'resource': self.resource}

    def get_eligible_targets(self):
        if get_swallower(self.combatant):
            return [self.combatant]
        ret = [e for e in Map.get().get_non_swallowed_allies(self.combatant) if type(type(e).cls) is not Class.MONSTER or (type(e).cls is not Class.MONSTER.UNDEAD and type(e).cls is not Class.MONSTER.CONSTRUCT)]
        if type(type(self.combatant).cls) is not Class.MONSTER or (type(self.combatant).cls is not Class.MONSTER.UNDEAD and type(self.combatant).cls is not Class.MONSTER.CONSTRUCT):
            ret.append(self.combatant)
        return ret

    def create_all(self, previous_action_in_dag=None):
        targets = self.get_eligible_targets()
        return [CureWounds(t, self) for t in targets]

    def create(self, target):
        return CureWounds(target, self)

    def calculate_threat_to_target(self, target, **kwargs):
        battle_map = Map.get()
        if get_swallower(target):
            return 0
        if battle_map.get_cartesian_distance_combatants(self.combatant, target) <= CureWoundsFactory.range:
            missing_hp = get_missing_hp(self.combatant)
            return min(missing_hp, avg_roll(self.heal_dice) + self.mod)
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
        return avg_roll(self.heal_dice) + self.mod  # The simplification here is ok


class CureWounds(Actoid, DirectThreat):
    def __init__(self, target, factory):
        Actoid.__init__(self, ActoidFlags.IS_SPELL)
        self.target = target
        self.factory = factory

    def __str__(self):
        return f"Cure Wounds on {self.target}"

    def shorthand_str(self):
        return "Cure Wounds"

    @map_position_toggled_cache
    def calculate_threat(self, **kwargs):
        return self.factory.calculate_threat_to_target(self.target)

    def clear_cache(self):
        self.calculate_threat.cache_clear()
        self.calculate_threat_delta.cache_clear()

    @map_toggled_cache_with_key(key=lambda self, modifiers, *args, **kwargs: hashkey(self.factory.name, tuple(modifiers.items()), tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        return self.factory.calculate_threat_to_target_delta(self.target, modifiers, *args, **kwargs)

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        if get_swallower(self.factory.combatant) and self.target is not self.factory.combatant:
            return None
        battle_map = Map.get()
        curr_coord = tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])
        if not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            free_coords_in_range = _get_free_coords_in_cartesian_range(
                battle_map.grid,
                battle_map.get_combatant_position(self.target).get(),
                distances,
                inflate_to_dist=self.factory.combatant.size.value,
                rng=CureWoundsFactory.range, combatant_id=self.factory.combatant.id)
            return free_coords_in_range
        elif battle_map.get_cartesian_distance_combatants(self.factory.combatant, self.target) <= CureWoundsFactory.range:
            return [curr_coord]
        return None

