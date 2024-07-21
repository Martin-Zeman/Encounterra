import numpy as np

from .spheric_aoe import SphericAoe
from ..battle_map import Map
from ..effects.aoe_effect import AoeEffect
from ..geometry import get_square_center


# The order of inheritance is important here
class AoeSphericEffect(SphericAoe, AoeEffect):

    def __init__(self, initiator, coord, radius):
        SphericAoe.__init__(self, coord, radius)
        AoeEffect.__init__(self, initiator)
