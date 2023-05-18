from simulator.actions.actoid import Actoid, ActoidFlags


class Dash(Actoid):
    def __init__(self):
        Actoid.__init__(self, actoid_flags=ActoidFlags.IS_DASH)
        self.name = "Dash"
