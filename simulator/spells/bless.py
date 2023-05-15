from functools import cache

from simulator.combatant_coords import CombatantCoords
from simulator.spells.spell import SpellStats
from simulator.effects.effect import Effect
from simulator.actions.actoid import Actoid, ActoidFlags
from simulator.threat_calculator import ThreatModifier, ThreatModifierFactory
from itertools import combinations


class BlessFactory(ThreatModifierFactory):
    level = 1
    range = SpellStats.Range.FEET_30.value
    target = SpellStats.Target.THREE_CREATURES
    duration = SpellStats.Duration.MINUTE
    concentration = True
    type = SpellStats.Type.BUFF
    dc = None
    dmg_type = None

    def __init__(self, action_type, caster, effect_tracker):
        self.action_type = action_type # QUICKENED_BLESS, BLESS
        self.caster = caster
        self.effect_tracker = effect_tracker

    def __str__(self):
        """
        Important for FSM building
        """
        return "BlessFactory"

    def find_best_args(self, combatant, battle_map):
        # TODO Deprecated
        # Iterate over all allies within range and try plugging the mods into their factories and pick three best
        # TODO Should this include action type? Cause for a twinned version you would need multiple targets
        return 0

    def create_best(self, combatant, battle_map):
        return Bless(self.find_best_args(combatant, battle_map), self)

    def get_eligible_targets(self, battle_map):
        return combinations(battle_map.get_enemies_within_radius(self.caster, BlessFactory.range), 3)

    def create_all(self, battle_map):
        targets = self.get_eligible_targets(battle_map)
        return [Bless(t, self) for t in targets]

    # def create_mock(self):
    #     return Bless(None, self)

    # def calculate_threat_approx(self, combatant, battle_map, *args, **kwargs):
    #     #  calculate the modification for all allies and them do * 3/#num_allies. And then * ROUND_HORIZON
    #     # TODO This should call the mod threat calculation of the attack factory for all the attacks
    #     return 0

    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        """
        Calculates the threat the factory is capable of dealing to a specific target.
        This is useful for calculating threat_in from the abilities of enemies
        """
        return 0


class Bless(Actoid, Effect, ThreatModifier):
    def __init__(self, targets, factory):
        super().__init__(ActoidFlags.IS_SPELL)
        self.targets = targets
        self.factory = factory

    def activate(self):
        # todo should check if not already under the influence of another bless
        self.factory.caster.is_concentrating = True
        for target in self.targets:
            for mod in target.saving_throws_dice_mod.values():
                mod.append('1d')
            target.to_hit_dice_mod.append('1d4')

    def deactivate(self):
        self.factory.caster.is_concentrating = False
        for target in self.targets:
            for mod in target.saving_throws_dice_mod.values():
                mod.remove('1d')
            target.to_hit_dice_mod.remove('1d4')

    def is_affecting(self, combatant, battle_map):
        return combatant in self.targets


    def clear_cache(self):
        self.calculate_threat.cache_clear()

    @cache
    def calculate_threat(self, combatant, battle_map, combatant_coords: CombatantCoords = None, *args, **kwargs):
        # TODO Multiply the threat increment by 3 for 3 rounds
        # TODO iterate over all abilities of the targets and try plugging the mods into their factories
        return 0
