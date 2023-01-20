from simulator.spells.spell import SpellStats
from simulator.effects.effect import Effect
from simulator.action_types import HasteAction
from simulator.action_types import Action, BonusAction
from simulator.actoid import Actoid


class Haste(Actoid, Effect):

    level = 3
    spell_range = SpellStats.Range.FEET_30
    target = SpellStats.Target.ONE_CREATURE
    duration = SpellStats.Duration.MINUTE
    concentration = True
    type = SpellStats.Type.BUFF
    dc = None
    dmg_type = None

    def __init__(self, action_type, targets, caster, effect_tracker):
        super().__init__(Actoid.Type.IS_SPELL)
        self.action_type = action_type
        self.targets = targets
        self.caster = caster
        self.effect_tracker = effect_tracker

    def activate(self):
        self.caster.is_concentrating = True
        for target in self.targets:
            target.ac += 2
            target.haste_actions = [HasteAction.HASTE_ATTACK, HasteAction.HASTE_DISENGAGE, HasteAction.HASTE_DASH, HasteAction.HASTE_HIDE]
            target.has_haste_action = True

    def deactivate(self):
        self.caster.is_concentrating = False
        for target in self.targets:
            target.ac -= 2
            target.haste_actions.clear()
            self.effect_tracker.create_post_haste_lethargy(target)
            target.has_haste_action = False

    def is_affecting(self, combatant):
        return combatant is self.target


    @staticmethod
    def calculate_threat_approx(combatant, battle_map, *args, **kwargs):
        # TODO
        return 0

    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        # TODO
        return 0
