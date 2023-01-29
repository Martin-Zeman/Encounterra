from functools import cache

ADVANTAGE = {
    20: 0.098,
    19: 0.191,
    18: 0.278,
    17: 0.359,
    16: 0.437,
    15: 0.510,
    14: 0.576,
    13: 0.639,
    12: 0.698,
    11: 0.751,
    10: 0.798,
    9: 0.840,
    8: 0.877,
    7: 0.910,
    6: 0.938,
    5: 0.960,
    4: 0.978,
    3: 0.990,
    2: 0.998,
    1: 1.000
}

DISADVANTAGE = {
    20: 0.002,
    19: 0.010,
    18: 0.022,
    17: 0.039,
    16: 0.062,
    15: 0.089,
    14: 0.123,
    13: 0.160,
    12: 0.202,
    11: 0.249,
    10: 0.303,
    9: 0.361,
    8: 0.424,
    7: 0.492,
    6: 0.564,
    5: 0.640,
    4: 0.723,
    3: 0.811,
    2: 0.903,
    1: 1.000,
}

STRAIGHT = {
    20: 0.050,
    19: 0.100,
    18: 0.150,
    17: 0.200,
    16: 0.250,
    15: 0.300,
    14: 0.350,
    13: 0.400,
    12: 0.450,
    11: 0.500,
    10: 0.550,
    9: 0.600,
    8: 0.650,
    7: 0.700,
    6: 0.750,
    5: 0.800,
    4: 0.850,
    3: 0.900,
    2: 0.950,
    1: 1.000
}

@cache
def find_advantage_eq_bonus(min_needed_roll):
    """
    Finds the equivalent bonus for a roll with advantage
    """
    assert min_needed_roll < 21, "An impossible needed roll"
    straight = STRAIGHT[min_needed_roll]
    min_diff = abs(ADVANTAGE[min_needed_roll] - straight)
    min_i = min_needed_roll
    for i in range(min_needed_roll + 1, 21):
        diff = abs(ADVANTAGE[i] - straight)
        if diff < min_diff:
            min_diff = diff
            min_i = i
        else:
            break
    return min_i - min_needed_roll


@cache
def find_disadvantage_eq_penalty(min_needed_roll):
    """
    Finds the equivalent penalty for a roll with disadvantage
    """
    assert min_needed_roll < 21, "An impossible needed roll"
    straight = STRAIGHT[min_needed_roll]
    min_diff = abs(straight - DISADVANTAGE[min_needed_roll])
    min_i = min_needed_roll
    for i in range(min_needed_roll - 1, 1, -1):
        diff = abs(straight - DISADVANTAGE[i])
        if diff < min_diff:
            min_diff = diff
            min_i = i
        else:
            break
    return min_i - min_needed_roll