import logging
from simulator.actoid import Actoid

logger = logging.getLogger(__name__)


class Movement(Actoid):
    STANDARD = 1
    DISENGAGE = 2
    DASH = 2

    def __init__(self, increment, movement_type, incurs_aoo):
        Actoid.__init__(self, type=Actoid.Type.IS_MOVEMENT)
        self.increment = increment
        self.movement_type = movement_type
        self.incurs_aoo = incurs_aoo

    # def is_targeted_combat_action(self):
    #     return False

    # def is_movement(self):
    #     return True


class MovementGenerator:

    def __init__(self, combatant, movement_type, path, incurs_aoo=True):
        self.combatant = combatant
        self.movement_type = movement_type
        self.path = path
        self.incurs_aoo = incurs_aoo

    def get_generator(self):
        try:
            while self.path and self.combatant.movement:
                self.combatant.movement -= 1
                yield Movement(self.path.pop(0), self.movement_type, self.incurs_aoo)
        except GeneratorExit:
            logger.debug("Movement generator interrupted")
