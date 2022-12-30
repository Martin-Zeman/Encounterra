from simulator.effects.limited_duration_effect import LimitedDurationEffect
class EffectTracker:
    """
    TODO: Could be the class that takes care of exceptional removal of effects (such as rage)
    """
    def __init__(self):
        self.effects = []

    def add(self, effect, originator):
        self.effects.append((effect, originator))

    def new_turn(self, combatant):
        """
        All effects with a fixed duration measurable in rounds end just before the beginning of one of your turns.
        :param combatant:
        :return:
        """
        for effect in self.effects:
            if isinstance(effect[0], LimitedDurationEffect) and effect[1] is combatant:
                effect[0].new_round()

    def reset(self):
        self.effects.clear()