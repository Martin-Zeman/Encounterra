import logging
from simulator.actions.actoid import Actoid
from simulator.action_types import Movement

logger = logging.getLogger(__name__)


class MovementIncrement(Actoid):
    def __init__(self, increment, incurs_aoo, factory):
        Actoid.__init__(self, actoid_type=Actoid.Type.IS_MOVEMENT)
        self.increment = increment
        self.incurs_aoo = incurs_aoo
        self.factory = factory


class MovementGenerator:

    def __init__(self, combatant, path, incurs_aoo=True, action_type=Movement.STANDARD):
        self.combatant = combatant
        self.path = path
        self.incurs_aoo = incurs_aoo
        self.action_type = action_type

    def get_generator(self):
        try:
            while self.path and self.combatant.movement:
                yield MovementIncrement(self.path.pop(0), self.incurs_aoo, self)
                # yield self.path.pop(0)
        except GeneratorExit:
            pass
