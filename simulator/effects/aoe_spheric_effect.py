from simulator.effects.effect import Effect

class AoeSphericEffect(Effect):

    def __init__(self, coord, radius):
        self.coord = coord
        self.radius = radius

    def on_enter(self, combatant):
        pass

    def on_start_of_turn(self, combatant):
        pass

    def on_end_of_turn(self, combatant):
        pass