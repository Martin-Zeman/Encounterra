class Attack:
    def __init__(self, to_hit, dmg_dice, dmg_bonus, is_bonus, crit_range=[20]):
        self.to_hit = to_hit
        self.dmg_dice = dmg_dice
        self.dmg_bonus = dmg_bonus
        self.is_bonus = is_bonus
        self.crit_range = crit_range