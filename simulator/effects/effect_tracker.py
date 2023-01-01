from simulator.effects.limited_duration_effect import LimitedDurationEffect
from simulator.effects.post_haste_lathargy import PostHasteLethargy
class EffectTracker:
    """
    TODO: Could be the class that takes care of exceptional removal of effects (such as rage)
    """
    def __init__(self):
        self.effects = []

    def add(self, effect, originator):
        self.effects.append((effect, originator))

    # def new_turn(self, combatant):
    #     """
    #     All effects with a fixed duration measurable in rounds end just before the beginning of one of your turns.
    #     :param combatant:
    #     :return:
    #     """
    #     for effect in self.effects:
    #         if isinstance(effect[0], LimitedDurationEffect) and effect[1] is combatant:
    #             effect[0].new_round()

    def new_turn(self):
        """
        All effects with a fixed duration measurable in rounds end just before the beginning of one of your turns.
        :param combatant:
        :return:
        """
        self.effects = [e for e in self.effects if not isinstance(e[0], LimitedDurationEffect) or e[0].new_round()]

    def get_all_affecting_combatant(self, combatant):
        """
        Returns all effects affecting a combatant as a set
        :param combatant:
        :return: set of all effects affecting a combatant
        """
        return {e[0] for e in self.effects if e[0].is_affecting(combatant)}

    def create_post_haste_lethargy(self, combatant):
        self.effects.append(PostHasteLethargy(combatant))

    def reset(self):
        for effect in self.effects:
            effect[0].deactivate()
        self.effects.clear()