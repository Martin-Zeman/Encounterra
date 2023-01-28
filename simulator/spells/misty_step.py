from simulator.spells.spell import SpellStats
import logging
from simulator.action_types import BonusAction, Action
from simulator.actions.actoid import Actoid
from simulator.threat_calculator import ThreatModifier, FactoryThreat
from simulator.combatant import Combatant

logger = logging.getLogger(__name__)

class MistyStepFactory(FactoryThreat):

    def __init__(self, caster):
        self.action_type = BonusAction.MISTY_STEP
        self.caster = caster

    def find_best_args(self, combatant, battle_map):
        if self.caster.archetype is Combatant.Archetype.MELEE:
            # TODO Improve this
            if self.caster.selected_enemy:
                free_coords = battle_map.get_free_coords_at_distance(self.caster.selected_enemy, 1, self.caster)
            return free_coords[0] if free_coords else 0
        elif self.caster.archetype is Combatant.Archetype.RAMGED:
            return battle_map.get_free_coords_away_from_enemies(combatant, MistyStep.spell_range.value)
        return 0

    def create_best(self, combatant, battle_map, **kwargs):
        return MistyStep(self.find_best_args(combatant, battle_map), self)

    def calculate_threat_approx(self, battle_map, *args, **kwargs):
        """
        Has two modes. One for melee and one for ranged characters. For melee it estimates the biggest difference in threat which the increased range
        can make.
        For a ranged character it estimates the potential dmg prevention from gaining distance.
        """
        if self.caster.archetype is Combatant.Archetype.MELEE:
            max_mod = 0
            for action in self.caster.actions:
                if action[0] is Action.ATTACK:
                    max_mod = max(max_mod, action[1].calculate_threat_approx_mod(self, battle_map, {'range': MistyStep.spell_range.value}, *args, **kwargs))
            for bonus_action in self.caster.bonus_actions:
                if bonus_action[0] is BonusAction.BONUS_ATTACK or bonus_action[0] is BonusAction.PAM_BONUS_ATTACK:
                    max_mod = max(max_mod, bonus_action[1].calculate_threat_approx_mod(self, battle_map, {'range': MistyStep.spell_range.value}, *args, **kwargs))
            return max_mod
        elif self.caster.archetype is Combatant.Archetype.RANGED:
            return 0 # TODO
        return 0

    def calculate_threat_approx_mod(self, battle_map, modified_stats, *args, **kwargs):
        return 0 # no need

    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
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

    def calculate_threat_mod(self, combatant, battle_map, *args, **kwargs):
        # TODO Add up all potential dmg from enemies that would normally be within their movement range
        # this can be arbitrated between other bonus action abilities
        return 0
