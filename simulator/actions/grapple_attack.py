from .action_types import HasteAction
from ..actions.actoid import FactoryFlags, Actoid, ActoidFlags
from ..battle_map import Map, _get_free_coords_in_hop_range
from ..conditions import Conditions, is_affected_by_any, is_affected_by, get_swallower, get_grappler
import logging

from ..threat_interfaces import AttackThreatModifier
from ..factory_interfaces import DirectThreatFactory
from ..threat_utils import calc_p_hit
from ..utils.roll_types import RollType

logger = logging.getLogger("Encounterra")


def s_affected_by_any(target, INCAPACITATED, RESTRAINED):
    pass


class GrappleAttackFactory(DirectThreatFactory):

    def __init__(self, action_type, name, combatant, to_hit, attack_range, dc, follow_up_attack):
        super().__init__()
        self.action_type = action_type
        self.name = name
        self.combatant = combatant
        self.to_hit = to_hit
        self.range = attack_range
        self.dc = dc
        self.follow_up_attack = follow_up_attack
        self.flags |= FactoryFlags.IS_MELEE
        self.flags |= FactoryFlags.IS_ATTACK_LIKE

    def get_ability_name(self):
        return f"Grapple Attack with {self.name}"

    def get_kwargs(self):
        return {'name': self.name, 'combatant': self.combatant, 'to_hit': self.to_hit}

    def get_eligible_targets(self):
        swallower = get_swallower(self.combatant)
        if swallower:
            return []
        return [e for e in Map.get().get_non_swallowed_enemies(self.combatant) if get_grappler(e) is not self.combatant]

    def create(self, target):
        return GrappleAttack(target, self)

    def create_all(self, previous_action_in_dag=None):
        targets = self.get_eligible_targets()
        return [GrappleAttack(t, self) for t in targets]

    def calculate_max_threat(self):
        targets = self.get_eligible_targets()
        max_threat = 0
        for target in targets:
            if s_affected_by_any(target, Conditions.INCAPACITATED, Conditions.RESTRAINED):
                continue  # TODO: This is specific to Vampire Spawn, consider removing it
            p_hit = calc_p_hit(self.follow_up_attack.to_hit, target.ac)
            max_threat = max(max_threat, p_hit * self.follow_up_attack.calculate_threat_to_target(target))
        return max_threat

    def calculate_threat_to_target(self, target, **kwargs):
        attack = kwargs["attack"]
        if attack.factory is self.follow_up_attack:
            grappler_of_target = get_grappler(target)
            if grappler_of_target is self.combatant:
                return 0  # Already grappled by this combatant, won't bring any extra threat
            if s_affected_by_any(target, Conditions.INCAPACITATED, Conditions.RESTRAINED):
                return 0

            p_hit = calc_p_hit(attack.factory.to_hit, target.ac)
            return p_hit * attack.factory.calculate_threat_to_target(target, **kwargs)
        else:
            return 0

    def calculate_threat_to_target_delta(self, target, modifiers, *args, **kwargs):
        # Assuming Action.VAMPIRIC_BITE only
        return self.follow_up_attack.calculate_threat_to_target_delta(target, modifiers, *args, **kwargs)


class GrappleAttack(AttackThreatModifier):

    def __init__(self, target, factory):
        AttackThreatModifier.__init__(self, ActoidFlags.IS_ATTACK_LIKE | ActoidFlags.IS_ACTION_ENABLER)
        self.target = target
        self.factory = factory
        self.roll_type = RollType.STRAIGHT

    def __str__(self):
        prefix = ""
        if isinstance(self.factory.action_type, HasteAction):
            prefix = "Hasted "
        return prefix + f"Grapple Attack on {self.target}"

    def shorthand_str(self):
        prefix = ""
        if isinstance(self.factory.action_type, HasteAction):
            prefix = "Hasted "
        return prefix + f"Grapple Attack"

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        swallower = get_swallower(self.factory.combatant)
        if swallower:
            return None
        if not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING, Conditions.RESTRAINED):
            return _get_free_coords_in_hop_range(
                battle_map.grid,
                battle_map.get_combatant_position(self.target).get(),
                distances,
                inflate_to_dist=self.factory.combatant.size.value,
                rng=self.factory.range,
                combatant_id=self.factory.combatant.id)
        elif battle_map.are_in_hop_range(self.factory.combatant, self.target, self.factory.range):
            return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]

    def calculate_threat_for_attack(self, combatant, attack, *args, **kwargs):
        if hasattr(attack, 'target'):  # Could be Nop TODO: Remove this?
            return self.factory.calculate_threat_to_target(attack.target, attack=attack)
        return 0

    def calculate_threat(self, **kwargs):
        return 0
