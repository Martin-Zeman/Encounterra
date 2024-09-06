from enum import Flag, auto, Enum


class RollType(Flag):
    STRAIGHT = auto()
    ADVANTAGE = auto()
    DISADVANTAGE = auto()

# Calculated by find_disadvantage_eq_penalty and find_advantage_eq_bonus. Gives the statistic approximation of advantage/disadvantage in
# terms of a flat bonus/penalty. This is dependent on the AC/DC threshold.
# def calculate_probability(target):
#     return max(0, min(1, (21 - target) / 20))
#
#
# def calculate_bonus(prob, target):
#     return round(prob * 20 - 21 + target)
#
#
# def main():
#     print("D&D 5e Advantage/Disadvantage Equivalent Bonus Calculator")
#     print("\nTarget | Normal | Advantage | Disadvantage")
#     print("--------|--------|-----------|-------------")
#
#     target = 1
#     while target < 21:
#         normal_prob = calculate_probability(target)
#         advantage_prob = 1 - (1 - normal_prob) ** 2
#         disadvantage_prob = normal_prob ** 2
#
#         normal_bonus = 0  # By definition, normal roll has no bonus
#         advantage_bonus = calculate_bonus(advantage_prob, target)
#         disadvantage_bonus = calculate_bonus(disadvantage_prob, target)
#
#         print(f"{target:6d} | {advantage_bonus:9d} | {disadvantage_bonus:11d}")
#         target += 1
#
#
# if __name__ == "__main__":
#     main()
ROLL_TYPE_DELTA = {
    RollType.STRAIGHT: {
        1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0, 15: 0, 16: 0, 17: 0, 18: 0, 19: 0, 20: 0
    },
    # The Advantage equivalent bonus for a needed roll of at least equal to the key
    RollType.ADVANTAGE: {
        1: 0, 2: 1, 3: 2, 4: 3, 5: 3, 6: 4, 7: 4, 8: 5, 9: 5, 10: 5, 11: 5, 12: 5, 13: 5, 14: 5, 15: 4, 16: 4, 17: 3, 18: 3, 19: 2, 20: 1
    },
    # The Disadvantage equivalent penalty for a needed roll of at least equal to the key
    RollType.DISADVANTAGE: {
        1: 0, 2: -1, 3: -2, 4: -3, 5: -3, 6: -4, 7: -4, 8: -5, 9: -5, 10: -5, 11: -5, 12: -5, 13: -5, 14: -5, 15: -4, 16: -4, 17: -3, 18: -3,
        19: -2, 20: -1
    }
}

# TODO This may be oversimplified, calculate a bit more thoroughly
ROLL_TYPE_CRIT_DELTA = {
    RollType.STRAIGHT: 1.0,
    RollType.ADVANTAGE: 2.0,
    RollType.DISADVANTAGE: 0.5
}


class ThreatModifierType(Enum):
    TO_HIT_FLAT = auto()
    TO_HIT_DIE = auto()
    ROLL_TYPE = auto()
    RANGE = auto()
    DMG_BONUS_FLAT = auto()
    DMG_BONUS_DIE = auto()
    CRIT_RANGE = auto()
    AUTO_CRIT = auto()
    TARGET_AC = auto()

