from simulator.action import Action
from simulator.actoid import Actoid


class Dodge(Action, Actoid):
    def __init__(self, combatant, action_class):
        Action.__init__(self, name="Dodge", combatant=combatant, action_class=action_class)
        Actoid.__init__(self, type=Actoid.Type.IS_DODGE)
