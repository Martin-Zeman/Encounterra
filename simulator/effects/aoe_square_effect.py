from .square_aoe import SquareAoe
from ..effects.aoe_effect import AoeEffect


# The order of inheritance is important here
class AoeSquareEffect(SquareAoe, AoeEffect):

    def __init__(self, initiator, origin, length):
        SquareAoe.__init__(self, origin, length)
        AoeEffect.__init__(self, initiator)

    def is_affecting(self, combatant):
        return False  # TODO
