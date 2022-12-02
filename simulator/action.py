class Action:
    """ Consider doing this by inheritance """
    # TYPES = {"ATTACK":1, "DODGE":2, "DASH":3, "HIDE":4, "SPELL":5, "ABILITY":6}
    TYPE = "ACTION"

    class ActionClasses:
        ACTION = 1
        BONUS_ACTION = 2
        REACTION = 3

    def __init__(self, name, character, action_type, action_class):
        self.__name = name
        self.character = character
        self.TYPE = action_type
        self.action_class = action_class
        self.targeted_combat_action = False
        self.is_aoe = False

    def get_type(self):
        return self.TYPE

    def get_name(self):
        return self.__name

    def is_action(self):
        return self.action_class == Action.ActionClasses.ACTION

    def is_bonus(self):
        return self.action_class == Action.ActionClasses.BONUS_ACTION

    def is_reaction(self):
        return self.action_class == Action.ActionClasses.REACTION

    def is_targeted_combat_action(self):
        return self.targeted_combat_action

    def activate(self):
        pass

    def deactivate(self):
        pass

    def reset(self):
        pass

    def is_movement(self):
        return False
