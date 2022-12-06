import logging
from simulator.action import Action

logger = logging.getLogger(__name__)

class Movement(Action):

    STANDARD = 1
    DISENGAGE = 2
    DASH = 2

    def __init__(self, increment, movement_type, incurs_aoo):
        self.increment = increment
        self.movement_type = movement_type
        self.incurs_aoo = incurs_aoo

    def is_targeted_combat_action(self):
        return False

    def is_movement(self):
        return True

class MovementGenerator:

    def __init__(self, character, movement_type, path, incurs_aoo):
        self.character = character
        self.movement_type = movement_type
        self.path = path
        self.incurs_aoo = incurs_aoo

    def get_generator(self):
        try:
            while self.path and self.character.movement:
                self.character.movement -= 1
                yield Movement(self.path.pop(0), self.movement_type, self.incurs_aoo)
        except GeneratorExit:
            logger.debug("Movement generator interrupted")

