from simulator.spells.spell import SpellStats
from simulator.effects.effect import Effect
from simulator.action_types import HasteAction
from simulator.action_types import Action, BonusAction
from simulator.actoid import Actoid
from simulator.threat_calculator import ThreatModifier, FactoryThreat
from simulator.misc import SavingThrow

class BlessFactory(FactoryThreat):
    def __init__(self, action_type, caster, effect_tracker):
        super().__init__(Actoid.Type.IS_SPELL)
        self.action_type = action_type # TWINNED_HASTE, QUICKENED_HASTE, HASTE
        self.caster = caster
        self.effect_tracker = effect_tracker

    def find_best_args(self, combatant, battle_map):
        # Iterate over all allies within range and try plugging the mods into their factories and pick three best
        # TODO Should this include action type? Cause for a twinned version you would need multiple targets
        return 0

    def create_best(self, combatant, battle_map):
        return Bless(self.find_best_args(combatant, battle_map), self)

    def calculate_threat_approx(self, combatant, battle_map, *args, **kwargs):
        #  calculate the modification for all allies and them do * 3/#num_allies. And then * ROUND_HORIZON
        return 0

    def calculate_threat_approx_mod(self, combatant, battle_map, modified_stats, *args, **kwargs):
        return 0



class Bless(Actoid, Effect, ThreatModifier):

    level = 1
    spell_range = SpellStats.Range.FEET_30
    target = SpellStats.Target.THREE_CREATURES
    duration = SpellStats.Duration.MINUTE
    concentration = True
    type = SpellStats.Type.BUFF
    dc = None
    dmg_type = None

    def __init__(self, targets, factory):
        super().__init__(Actoid.Type.IS_SPELL)
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

    def is_affecting(self, combatant):
        return combatant is self.target

    def calculate_threat_mod(self, combatant, battle_map, *args, **kwargs):
        # TODO Multiply the threat increment by 3 for 3 rounds
        # TODO iterate over all abilities of the targets and try plugging the mods into their factories
        return 0
