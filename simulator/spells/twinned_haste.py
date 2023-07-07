import logging
from itertools import combinations

from simulator.battle_map import Map
from simulator.spells.spell import SpellStats
from simulator.effects.effect import Effect, EffectType
from simulator.actions.actoid import Actoid, ActoidFlags
from simulator.threat_utils import mean_dmg
from simulator.threat_interfaces import ThreatModifier, ThreatModifierFactory
from functools import reduce
from simulator.misc import ROUND_HORIZON, get_attacks, get_haste_eligile_attacks, Conditions
from simulator.spells.haste import HasteFactory
from simulator.utils.roll_types import ThreatModifierType

logger = logging.getLogger("EncounTroll")

class TwinnedHasteFactory(ThreatModifierFactory):
    level = 3
    range = SpellStats.Range.FEET_30.value
    target = SpellStats.Target.ONE_CREATURE
    duration = SpellStats.Duration.MINUTE
    concentration = True
    type = SpellStats.Type.BUFF
    dc = None
    dmg_type = None

    def __init__(self, action_type, caster):
        super().__init__()
        self.action_type = action_type # TWINNED_HASTE, QUICKENED_HASTE, HASTE
        self.combatant = caster

    def __str__(self):
        """
        Important for FSM building
        """
        return "TwinnedHasteFactory"


    def get_eligible_targets(self):
        swallower = self.combatant.get_swallower()
        if swallower:
            return [self.combatant, None]
        battle_map = Map.get()
        ret = [a for a in battle_map.get_allies_within_radius(self.combatant, HasteFactory.range) if not a.is_affected_by(Conditions.SWALLOWED)]
        ret.append(self.combatant)
        ret = [a for a in ret if len(a.haste_action_factories) == 0]
        ret = combinations(ret, 2)
        return ret

    def create_all(self):
        targets = self.get_eligible_targets()
        return [TwinnedHaste(t, self) for t in targets]

    def create(self, targets):
        return TwinnedHaste(targets, self)

    def calculate_threat_to_target(self, target, *args, **kwargs):
        """
        For the given target ally it finds the attack with the highest mean dmg across all enemies withing range. It then adds
        estimated dmg prevention given by the AC bonus and by the saving throw advantage.
        """
        if target.haste_action_factories:  # No benefit if already hasted
            return 0
        battle_map = Map.get()
        enemies = battle_map.get_enemies(target)
            # This doesn't take different attack ranges into account
        max_attack_dmg = 0
        attacks = get_haste_eligile_attacks(target)
        for attack in attacks:
            potential_targets = battle_map.get_enemies_within_hop_distance(target, target.speed + attack.range + 1)
            if not potential_targets:
                continue
            dmg_acc = reduce(lambda acc, pt: acc + mean_dmg(attack.to_hit, attack.dmg_dice, attack.dmg_bonus, pt.ac, attack.crit_range, pt.is_resistant_to(attack.dmg_type)), potential_targets, 0)
            dmg_acc /= len(potential_targets)
            max_attack_dmg = max(dmg_acc, max_attack_dmg)
        attack_dmg_decrement_acc = 0
        for enemy in enemies:
            enemy_attacks = get_attacks(enemy)
            if not enemy_attacks:
                continue
            attack_dmg_decrement_acc = reduce(lambda acc, at: acc + at.calculate_threat_to_target_delta(target, {ThreatModifierType.TARGET_AC: 2}), enemy_attacks, 0)
            attack_dmg_decrement_acc /= len(enemy_attacks)

            # TODO include the ST-based abilities here
        max_attack_dmg -= attack_dmg_decrement_acc  # Take care to subtract this, because the decrement is non-positive
        return max_attack_dmg * ROUND_HORIZON


class TwinnedHaste(Actoid, Effect, ThreatModifier):

    def __init__(self, targets, factory):
        super().__init__(ActoidFlags.IS_SPELL)
        self.targets = targets
        self.factory = factory

    def __str__(self):
        return f"Twinned Haste on {self.targets[0]} and {self.targets[1]}"

    def get_effect_type(self):
        return EffectType.TWINNED_HASTE

    def shorthand_str(self):
        return "Twinned Haste"

    def activate(self):
        Map.get().effect_tracker.add(self)
        self.factory.combatant.concentration_effect = self
        for target in self.targets:
            target.ac += 2
            target.add_hasted_factories()
            target.has_haste_action = True  # TODO Remove this

    def deactivate(self):
        effect_tracker = Map.get().effect_tracker
        self.factory.combatant.break_concentration()
        for target in self.targets:
            target.ac -= 2
            target.haste_action_factories.clear()
            effect_tracker.create_post_haste_lethargy(target)
            target.has_haste_action = False  # TODO Remove this

    def is_affecting(self, combatant):
        return combatant in self.targets


    def calculate_threat(self, **kwargs):
        """
        For the given target ally it finds the attack with the highest mean dmg across all enemies withing range. It then adds
        estimated dmg prevention given by the AC bonus and by the saving throw advantage.
        """
        assert not(self.targets[0] is None and self.targets[1] is None), "Both of the twinned haste targets are None. This should not happen, there should always be at least self as target"
        target1_threat = self.factory.calculate_threat_to_target(self.targets[0]) if self.targets[0] is not None else 0
        target2_threat = self.factory.calculate_threat_to_target(self.targets[1]) if self.targets[1] is not None else 0
        ret = target1_threat + target2_threat
        logger.info(f"MY DEBUG {self} threat = {ret}")
        return ret

    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        if self.targets[0] is self.factory.combatant:
            coords_for_first = battle_map.get_all_accessible_coords(shortest_paths, self.factory.combatant)
        else:
            coords_for_first = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.targets[0]),
                                                                             distances,
                                                                             inflate_to_size=self.factory.combatant.size,
                                                                             rng=TwinnedHasteFactory.range)

        if self.targets[1] is self.factory.combatant:
            coords_for_second = battle_map.get_all_accessible_coords(shortest_paths, self.factory.combatant)
        else:
            coords_for_second = battle_map.get_free_coords_in_cartesian_range(battle_map.get_combatant_position(self.targets[1]),
                                                                              distances,
                                                                              inflate_to_size=self.factory.combatant.size,
                                                                              rng=TwinnedHasteFactory.range)
        return coords_for_first.intersection(coords_for_second)

    def is_current_coord_eligible(self):
        if self.factory.combatant.get_swallower():
            return False  # Technically possible but doesn't make sense to waste the sorcery points
        battle_map = Map.get()
        return battle_map.get_cartesian_distance(self.factory.combatant, self.targets[0]) <= TwinnedHasteFactory.range and \
            battle_map.get_cartesian_distance(self.factory.combatant, self.targets[1]) <= TwinnedHasteFactory.range
