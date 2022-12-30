from simulator.actoid import Actoid


class Dodge(Actoid):
    def __init__(self, combatant):
        Actoid.__init__(self, type=Actoid.Type.IS_DODGE)
        self.name = "Dodge"
        self.combatant = combatant
