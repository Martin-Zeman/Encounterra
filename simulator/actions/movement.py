import logging
import numpy as np
from simulator.actions.actoid import Actoid, ActoidFlags
from simulator.action_types import Movement

logger = logging.getLogger(__name__)


class MovementIncrement(Actoid):
    def __init__(self, increment, incurs_aoo, factory):
        Actoid.__init__(self, actoid_type=ActoidFlags.IS_MOVEMENT)
        self.increment = increment
        self.incurs_aoo = incurs_aoo
        self.factory = factory

    def __str__(self):
        return np.array2string(self.increment)


class MovementGenerator:

    def __init__(self, combatant, path, action_type=Movement.STANDARD):
        self.combatant = combatant
        self.path = path
        self.action_type = action_type

    def get_generator(self):
        try:
            while self.path and self.combatant.movement:
                yield MovementIncrement(self.path.pop(0), not self.combatant.has_disengaged, self)
                # yield self.path.pop(0)
        except GeneratorExit:
            pass
