from simulator.actions.actoid import Actoid, ActoidFlags
from simulator.action_types import Action

class Dash(Actoid):
    def __init__(self):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_DASH, action_type=Action.DASH)
        self.name = "Dash"
