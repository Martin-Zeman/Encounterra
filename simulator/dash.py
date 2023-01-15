from simulator.actoid import Actoid
from simulator.action_types import Action

class Dash(Actoid):
    def __init__(self):
        Actoid.__init__(self, actoid_type=Actoid.Type.IS_DASH, action_type=Action.DASH)
        self.name = "Dash"
