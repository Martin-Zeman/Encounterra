from simulator.action import Action

class Dodge(Action):
    def __init__(self, name, character, action_class):
        Action.__init__(self, name, character, "DODGE", action_class)
