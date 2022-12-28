import logging
from simulator.actoid import Actoid

logger = logging.getLogger(__name__)


class MovementIncrement(Actoid):
    def __init__(self, increment, incurs_aoo):
        Actoid.__init__(self, type=Actoid.Type.IS_MOVEMENT)
        self.increment = increment
        self.incurs_aoo = incurs_aoo


class MovementGenerator:

    def __init__(self, combatant, path, incurs_aoo=True):
        self.combatant = combatant
        self.path = path
        self.incurs_aoo = incurs_aoo

    def get_generator(self):
        try:
            while self.path and self.combatant.movement:
                # yield Movement(self.path.pop(0), self.movement_type, self.incurs_aoo)
                yield self.path.pop(0)
        except GeneratorExit:
            logger.debug("Movement generator exhausted")
