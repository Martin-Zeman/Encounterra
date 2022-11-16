class Action:
    """ Consider doing this by inheritance """
    TYPES = {"ATTACK":1, "DODGE":2, "DASH":3, "HIDE":4, "SPELL":5, "ABILITY":6}

    def __init__(self, action_type, name, target_name):
        self.action_type = action_type
        self.name = name
        self.attack = None
        self.target_name = target_name

    def __init__(self, attack, name, target_name):
        self.action_type = "ATTACK"
        self.name = name
        self.attack = attack
        self.target_name = target_name

    def get_type(self):
        return self.action_type

    def get_name(self):
        return self.name

    def get_attack(self):
        return self.attack

    def get_target_name(self):
        return self.target_name