from .action_types import Action
from ..actions.actoid import FactoryFlags, Actoid, ActoidFlags
from ..battle_map import Map
from ..misc import Conditions
import logging

from ..threat_interfaces import AttackThreatModifier, Factory
from ..threat_utils import calc_p_hit
from ..utils.roll_types import RollType

logger = logging.getLogger("Encounterra")


class GrappleAttackFactory(Factory):

    def __init__(self, action_type, name, combatant, to_hit):
        super().__init__()
        self.action_type = action_type
        self.name = name
        self.combatant = combatant
        self.to_hit = to_hit
        self.flags |= FactoryFlags.IS_MELEE
        self.flags |= FactoryFlags.IS_ATTACK_LIKE

    def get_ability_name(self):
        return f"Grapple Attack with {self.name}"

    def get_kwargs(self):
        return {'name': self.name, 'combatant': self.combatant, 'to_hit': self.to_hit}

    def get_eligible_targets(self):
        swallower = self.combatant.get_swallower()
        if swallower:
            return []
        return [e for e in Map.get().get_enemies(self.combatant) if not e.is_affected_by(Conditions.SWALLOWED)]

    def create(self, target):
        return GrappleAttack(target, self)

    def create_all(self, previous_action_in_dag=None):
        targets = self.get_eligible_targets()
        return [GrappleAttack(t, self) for t in targets]


class GrappleAttack(Actoid, AttackThreatModifier):

    def __init__(self, target, factory):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_ATTACK_LIKE)
        self.target = target
        self.factory = factory
        self.roll_type = RollType.STRAIGHT

    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
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

    def calculate_threat_for_attack(self, combatant, attack, *args, **kwargs):
        """
        The conditional nature of the follow-up attack is modeled by moving all the entire threat contribution to this
        threat modifier attack. Which means the attack itself also needs to take this into account.
        """
        if attack.action_type is Action.VAMPIRIC_BITE:
            grappler_of_target = attack.target.get_grappler()
            if grappler_of_target is self.factory.combatant:
                return 0  # Already grappled by this combatant, won't bring any extra threat
            if attack.target.is_affected_by_any(Conditions.INCAPACITATED, Conditions.RESTRAINED):
                return 0

            p_hit = calc_p_hit(attack.factory.to_hit, attack.target.ac)
            return p_hit * attack.factory.calculate_threat_to_target(attack.target, kwargs)
        else:
            return 0

    def calculate_threat(self, **kwargs):
        return 0
