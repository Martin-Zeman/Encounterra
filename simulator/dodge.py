from simulator.actoid import Actoid
from simulator.action_types import Action

class Dodge(Actoid):
    def __init__(self, combatant):
        Actoid.__init__(self, actoid_type=Actoid.Type.IS_DODGE)
        self.action_type = Action.DODGE
        self.name = "Dodge"
        self.combatant = combatant
