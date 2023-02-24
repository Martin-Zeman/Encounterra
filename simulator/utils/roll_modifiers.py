from enum import Flag, auto


class RollModifier(Flag):
    STRAIGHT = auto()
    ADVANTAGE = auto()
    DISADVANTAGE = auto()

# Calculated by find_disadvantage_eq_penalty and find_advantage_eq_bonus. Gives the statistic approximation of advantage/disadvantage in
# terms of a flat bonus/penalty. This is dependent on the AC/DC threshold.
ROLL_MODIFIER = {
    RollModifier.STRAIGHT: {
        1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0, 15: 0, 16: 0, 17: 0, 18: 0, 19: 0, 20: 0
    },
    # The Advantage equivalent bonus for a needed roll of at least equal to the key
    RollModifier.ADVANTAGE: {
        1: 0, 2: 3, 3: 4, 4: 5, 5: 5, 6: 5, 7: 5, 8: 5, 9: 5, 10: 4, 11: 4, 12: 4, 13: 3, 14: 3, 15: 3, 16: 2, 17: 2, 18: 1, 19: 1, 20: 0
    },
    # The Disadvantage equivalent penalty for a needed roll of at least equal to the key
    RollModifier.DISADVANTAGE: {
        1: 0, 2: 0, 3: -1, 4: -1, 5: -2, 6: -2, 7: -3, 8: -3, 9: -3, 10: -4, 11: -4, 12: -4, 13: -5, 14: -5, 15: -5, 16: -5, 17: -5, 18: -5,
        19: -4, 20: -3
    }
}

# TODO This may be oversimplified, calculate a bit more thoroughly
ROLL_MODIFIER_CRIT = {
    RollModifier.STRAIGHT: 1.0,
    RollModifier.ADVANTAGE: 2.0,
    RollModifier.DISADVANTAGE: 0.5
}