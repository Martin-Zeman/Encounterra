from simulator.action import Action


class Ability(Action):

    def __init__(self, name, character, uses, action_class):
        super().__init__(name, character, "ABILITY", action_class)
        self.max_uses = uses
        self.curr_uses = uses
        self.active = False

    def is_active(self):
        return self.active

    def has_uses(self):
        return self.curr_uses > 0

    def reset(self):
        self.curr_uses = self.max_uses
        self.active = False
