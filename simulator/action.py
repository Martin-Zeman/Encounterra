class Action:
    """ Consider doing this by inheritance """
    # TYPES = {"ATTACK":1, "DODGE":2, "DASH":3, "HIDE":4, "SPELL":5, "ABILITY":6}
    TYPE = "ACTION"

    def __init__(self, name, character, action_type, action_class):
        self.__name = name
        self.character = character
        self.TYPE = action_type
        self.action_class = action_class
        self.targeted_combat_action = False
        # self.attack = None
        # self.target_name = target_name

    # def __init__(self, attack, name, target_name):
    #     self.action_type = "ATTACK"
    #     self.name = name
    #     self.attack = attack
    #     self.target_name = target_name

    def get_type(self):
        return self.TYPE

    def get_name(self):
        return self.__name

    def is_bonus(self):
        return self.action_class == "bonus_action"

    def is_targeted_combat_action(self):
        return self.targeted_combat_action

    def activate(self):
        pass

    def deactivate(self):
        pass

    def reset(self):
        pass

    # def get_attack(self):
    #     return self.attack
    #
    # def get_target_name(self):
    #     return self.target_name