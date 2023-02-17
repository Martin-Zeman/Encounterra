from simulator.spells.spell import SpellStats
import logging
from simulator.action_types import BonusAction, Action
from simulator.actions.actoid import Actoid
from simulator.threat_calculator import ThreatModifier, DirectThreatFactory
from simulator.misc import CombatantArchetype, DistanceMetric

logger = logging.getLogger(__name__)

class MistyStepFactory(DirectThreatFactory):

    def __init__(self, caster):
        self.action_type = BonusAction.MISTY_STEP
        self.caster = caster

    def find_best_args(self, combatant, battle_map):
        free_coords = None
        if self.caster.archetype is CombatantArchetype.MELEE:
            # TODO Improve this
            if self.caster.selected_enemy:
                free_coords = battle_map.get_free_coords_at_distance(self.caster.selected_enemy, self.caster, 1)
            return free_coords[0] if free_coords else None
        elif self.caster.archetype is CombatantArchetype.RANGED:
            free_coords = battle_map.get_free_coords_away_from_enemies(combatant, MistyStep.spell_range.value,  DistanceMetric.CARTESIAN)
            return free_coords[0] if free_coords else None
        return None

    def create_best(self, combatant, battle_map):
        best_args = self.find_best_args(combatant, battle_map)
        if best_args is None:
            return None
        return MistyStep(best_args, self)

    def create(self, coord):
        return MistyStep(coord, self)

    def calculate_threat_approx_mod(self, battle_map, modified_stats, *args, **kwargs):
        return 0 # no need

    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        """
        TODO could calculate the dmg difference if we get out of range or the possibility of getting into range
        """
        if self.caster.archetype is CombatantArchetype.MELEE:
            max_mod = 0
            for action in self.caster.actions:
                if action[0] is Action.ATTACK:
                    max_mod = max(max_mod, action[1].calculate_threat_approx_mod(self, battle_map, {'range': MistyStep.spell_range.value + self.caster.movement}, *args, **kwargs))
            for bonus_action in self.caster.bonus_actions:
                if bonus_action[0] is BonusAction.BONUS_ATTACK or bonus_action[0] is BonusAction.PAM_BONUS_ATTACK:
                    max_mod = max(max_mod, bonus_action[1].calculate_threat_approx_mod(self, battle_map, {'range': MistyStep.spell_range.value + self.caster.movement}, *args, **kwargs))
            return max_mod
        elif self.caster.archetype is CombatantArchetype.RANGED:
            enemies = battle_map.get_enemies(self.caster)
            max_threat_before = 0
            max_threat_after = 0
            for enemy in enemies:
                factories = enemy.action_factories.extend(enemy.bonus_action_factories).extend(enemy.haste_action_factories)
                max_threat_before = max([f.calculate_threat_to_target(battle_map, self.caster) for f in factories])
                with battle_map.as_if_dist_mod_from_combatant(self.caster, enemy, self.caster.movement + MistyStep.spell_range.value):
                    max_threat_after = max([f.calculate_threat_to_target(battle_map, self.caster) for f in factories])
            return max_threat_after - max_threat_before
        return 0

    def calculate_threat_to_target_mod(self, battle_map, target, modified_stats, *args, **kwargs):
        return 0


class MistyStep(Actoid, ThreatModifier):

    level = 2
    spell_range = SpellStats.Range.FEET_30
    target = SpellStats.Target.SELF
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = False
    type = SpellStats.Type.OTHER
    dc = None
    dmg_type = None

    def __init__(self, coord, factory):
        super().__init__(Actoid.Type.IS_SPELL)
        self.coord = coord
        self.factory = factory

    def __str__(self):
        return "Misty Step"

    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        # TODO Add up all potential dmg from enemies that would normally be within their movement range
        # this can be arbitrated between other bonus action abilities
        if self.factory.caster.archetype is CombatantArchetype.MELEE:
            max_mod = 0
            # TODO use similar approach as below but compare dmg to targets in range at both positions
            # for action in self.factory.caster.actions:
            #     if action[0] is Action.ATTACK:
            #         max_mod = max(max_mod, action[1].calculate_threat_approx_mod(self, battle_map, {'range': MistyStep.spell_range.value + self.caster.movement}, *args, **kwargs))
            # for bonus_action in self.factory.caster.bonus_actions:
            #     if bonus_action[0] is BonusAction.BONUS_ATTACK or bonus_action[0] is BonusAction.PAM_BONUS_ATTACK:
            #         max_mod = max(max_mod, bonus_action[1].calculate_threat_approx_mod(self, battle_map, {'range': MistyStep.spell_range.value + self.caster.movement}, *args, **kwargs))
            return max_mod
        elif self.factory.caster.archetype is CombatantArchetype.RANGED:
            enemies = battle_map.get_enemies(self.factory.caster)
            max_threat_before = 0
            max_threat_after = 0
            for enemy in enemies:
                factories = enemy.action_factories
                factories.extend(enemy.bonus_action_factories)
                factories.extend(enemy.haste_action_factories)
                max_threat_before = max([f[1].calculate_threat_to_target(battle_map, self.factory.caster) for f in factories])
                with battle_map.as_if_combatant_position(self.factory.caster, self.coord):
                    max_threat_after = max([f[1].calculate_threat_to_target(battle_map, self.factory.caster) for f in factories])
            return max_threat_after - max_threat_before
        return 0
