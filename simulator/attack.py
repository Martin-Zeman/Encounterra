from simulator.action import Action

class Attack(Action):
    def __init__(self, name, character, to_hit, dmg_dice, dmg_bonus, action_class, dmg_type, range, crit_range=[20]):
        Action.__init__(self, name, character, "ATTACK", action_class)
        self.to_hit = to_hit
        self.dmg_dice = dmg_dice
        self.dmg_bonus = dmg_bonus
        self.__dmg_type = dmg_type
        self.range = range
        self.crit_range = crit_range
        self.__target_name = ""
        self.targeted_combat_action = True
        self.advantage = False
        # TODO: Consider having the num of attacks here

    def set_target_character(self, target):
        self.__target_character = target

    def get_target_character(self):
        return self.__target_character

    # def get_instance(self):
    #     return copy.deepcopy(self)

    def get_dmg_type(self):
        return self.__dmg_type
