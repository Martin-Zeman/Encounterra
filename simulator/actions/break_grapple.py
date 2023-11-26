from ..actions.action_types import Action
from ..actions.actoid import Actoid, ActoidFlags


class BreakGrappleFactory:
    def __init__(self, grapple_condition):
        self.action_type = Action.BREAK_GRAPPLE
        self.grapple_condition = grapple_condition

    def create(self):
        return BreakGrapple(self)


class BreakGrapple(Actoid):
    def __init__(self, factory):
        Actoid.__init__(self, ActoidFlags.IS_BREAK_GRAPPLE)
        self.factory = factory

    def __str__(self):
        return "Break Grapple"

    def shorthand_str(self):
        return "Break Grapple"