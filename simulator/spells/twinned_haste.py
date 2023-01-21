from simulator.spells.spell import SpellStats
from simulator.effects.effect import Effect
from simulator.action_types import HasteAction
from simulator.action_types import Action, BonusAction
from simulator.actoid import Actoid
from simulator.threat_calculator import ThreatModifier


class TwinnedHasteFactory:
    def __init__(self, action_type, caster, effect_tracker):
        super().__init__(Actoid.Type.IS_SPELL)
        self.action_type = action_type  # TWINNED_HASTE, QUICKENED_HASTE, HASTE
        self.caster = caster
        self.effect_tracker = effect_tracker

    def find_best_args(self, combatant, battle_map):
        potential_targets = battle_map.get_allies_within_radius(combatant, TwinnedHaste.spell_range.value)
        # TODO finish this
        try:
            target2 = potential_targets[1][0]
        except IndexError:
            target2 = None
        return potential_targets[0][0], target2

    def create_best(self, combatant, battle_map):
        return TwinnedHaste(self.find_best_args(combatant, battle_map), self)


class TwinnedHaste(Actoid, Effect, ThreatModifier):
    level = 3
    spell_range = SpellStats.Range.FEET_30
    target = SpellStats.Target.ONE_CREATURE
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
        self.factory.caster.is_concentrating = True
        for target in self.targets:
            target.ac += 2
            target.haste_actions = [HasteAction.HASTE_ATTACK, HasteAction.HASTE_DISENGAGE, HasteAction.HASTE_DASH, HasteAction.HASTE_HIDE]
            target.has_haste_action = True

    def deactivate(self):
        self.factory.caster.is_concentrating = False
        for target in self.targets:
            target.ac -= 2
            target.haste_actions.clear()
            self.factory.effect_tracker.create_post_haste_lethargy(target)
            target.has_haste_action = False

    def is_affecting(self, combatant):
        return combatant is self.target

    @staticmethod
    def calculate_threat_mod_approx(combatant, battle_map, actions, *args, **kwargs):
        max_threat = 0
        potential_targets = battle_map.get_enemies_within_hop_distance(combatant, combatant.speed)
        best_attack
        dmg_acc = accumulate(potential_targets,
                             lambda pt: dmg_increment_for_dmg_flat(best_attack.to_hit, best_attack.dmg_dice, best_attack.dmg_bonus, pt.ac,
                                                                   self.rage_bonus)
        dmg_acc /= len(potential_targets)
        # TODO add avg dmg prevention
        return max_threat

    def calculate_threat_mod(self, combatant, battle_map, actions, *args, **kwargs):
        return mean_dmg(self.factory.to_hit, self.factory.dmg_dice, self.factory.dmg_bonus, self.target_combatant.ac,
                        len(self.factory.crit_range),
                        self.target_combatant.is_resistant_to(self.factory.dmg_type))
