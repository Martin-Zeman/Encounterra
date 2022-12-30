from simulator.effects.effect import Effect

class SphericEffect(Effect):

    def __init__(self, coord, radius):
        self.coord = coord
        self.radius = radius