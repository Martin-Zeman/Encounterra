
class Action:
    """ Consider doing this by inheritance """
    # TYPES = {"ATTACK":1, "DODGE":2, "DASH":3, "HIDE":4, "SPELL":5, "ABILITY":6}
    TYPE = "ACTION"

    class ActionClasses:
        ACTION = 1
        BONUS_ACTION = 2
        REACTION = 3

    def __init__(self, name, combatant, action_class):
        self.name = name
        self.combatant = combatant
        self.action_class = action_class
        self.targeted_combat_action = False
        self.is_aoe = False

    def get_name(self):
        return self.name

    def is_action(self):
        return self.action_class == Action.ActionClasses.ACTION

    def is_bonus(self):
        return self.action_class == Action.ActionClasses.BONUS_ACTION

    def is_reaction(self):
        return self.action_class == Action.ActionClasses.REACTION

    def activate(self):
        pass

    def deactivate(self):
        pass

    def reset(self):
        pass

    # def is_movement(self):
    #     return False
