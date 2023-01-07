from simulator.spells.spell import Spell
from simulator.effects.effect import Effect
from simulator.actions import HasteAction
from simulator.actions import Action, BonusAction


class Haste(Spell, Effect):
    def __init__(self, action_type, targets, caster, effect_tracker, level=3):
        level = min(max(level, 3), 9)
        super().__init__(level=level,
                         spell_range=Spell.Range.FEET_30,
                         target=Spell.Target.ONE_CREATURE,
                         duration=Spell.Duration.MINUTE,
                         concentration=True,
                         type=Spell.Type.HARMFUL,
                         dc=None,
                         dmg_type=None)
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
