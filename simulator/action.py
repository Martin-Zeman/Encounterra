class Action:
    """ Consider doing this by inheritance """
    # TYPES = {"ATTACK":1, "DODGE":2, "DASH":3, "HIDE":4, "SPELL":5, "ABILITY":6}
    TYPE = "ACTION"

    def __init__(self, action_type, name):
        self.TYPE = action_type
        self.__name = name
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

    # def get_attack(self):
    #     return self.attack
    #
    # def get_target_name(self):
    #     return self.target_name