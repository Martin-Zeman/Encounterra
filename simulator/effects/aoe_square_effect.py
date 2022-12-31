from simulator.effects.effect import Effect


class AoeSquareEffect(Effect):

    def __init__(self, origin, length):
        self.origin = origin
        self.length = length

    def is_affecting(self, combatant):
        return False  # TODO
