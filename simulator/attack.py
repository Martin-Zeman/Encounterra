from simulator.actoid import Actoid
from simulator.actions import Action

class Attack(Actoid):
    def __init__(self, name, combatant, target_combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, crit_range=[20]):
        Actoid.__init__(self, actoid_type=Actoid.Type.IS_ATTACK_LIKE_ACTION)
        self.action_type = Action.ATTACK
        self.name = name
        self.combatant = combatant
        self.target_combatant = target_combatant
        self.to_hit = to_hit
        self.dmg_dice = dmg_dice
        self.dmg_bonus = dmg_bonus
        self.dmg_type = dmg_type
        self.range = attack_range
        self.crit_range = crit_range
        self.targeted_combat_action = True
        self.advantage = False
        # TODO: Consider having the num of attacks here

    def set_target_combatant(self, target):
        self.target_combatant = target

    def get_target_combatant(self):
        return self.target_combatant

    def get_dmg_type(self):
        return self.dmg_type
