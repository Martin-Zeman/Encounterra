from functools import cache, reduce
from scipy.stats import randint
from simulator.misc import parse_dmg_dice
from simulator.utils.roll_modifiers import RollModifier


@cache
def mean_dmg(to_hit, dmg_dice, dmg_bonus, ac, crit_range=1, is_resistant=False):
    """
    Calculates mean dmg of an attack-like ability
    @param to_hit: to hit bonus
    @param dmg_dice: damage dice in a string form
    @param dmg_bonus: bonus to damage
    @param ac: target's AC
    @param crit_range: 1 - default for nat 20, 2 for [19, 20], 3 for [18..20], etc.
    @param is_resistant: True if the target is resistant to the dmg type
    @return: mean damage not accounting for critical failures
    """
    rv = randint(1, 21, to_hit)
    p_hit = 1.0 - rv.cdf(ac - 1)
    dice = parse_dmg_dice(dmg_dice)
    avg_dmg_die_roll = reduce(lambda acc, d: acc + d[0] * ((1.0 + d[1]) / 2.0), dice, 0)
    res = (avg_dmg_die_roll + dmg_bonus) * p_hit + 0.05 * crit_range * avg_dmg_die_roll
    return res if not is_resistant else (res / 2)


@cache
def dmg_increment_for_to_hit_flat(to_hit, dmg_dice, dmg_bonus, ac, to_hit_increment, crit_range=1,  is_resistant=False):
    """
    Calculates the increase in mean dmg for an attack-like ability using a flat to-hit bonus
    @param to_hit: to hit bonus
    @param dmg_dice: damage dice in a string form
    @param dmg_bonus: bonus to damage
    @param ac: target's AC
    @param to_hit_increment:
    @return: mean damage increment not accounting for critical failures
    """
    return mean_dmg(to_hit + to_hit_increment, dmg_dice, dmg_bonus, ac, crit_range, is_resistant) - mean_dmg(to_hit, dmg_dice, dmg_bonus, ac, crit_range, is_resistant)

@cache
def dmg_increment_for_dmg_flat(to_hit, dmg_dice, dmg_bonus, ac, dmg_increment):
    """
    Calculates the increase in mean dmg for an attack-like ability using a flat damage bonus
    @param to_hit: to hit bonus
    @param dmg_dice: damage dice in a string form
    @param dmg_bonus: bonus to damage
    @param ac: target's AC
    @param dmg_increment:
    @return: mean damage increment not accounting for critical failures
    """
    return mean_dmg(to_hit, dmg_dice, dmg_bonus + dmg_increment, ac) - mean_dmg(to_hit, dmg_dice, dmg_bonus, ac)


@cache
def dmg_decrement_for_ac_flat(to_hit, dmg_dice, dmg_bonus, ac, ac_bonus, crit_range=1,  is_resistant=False):
    """
    Calculates the decrease in mean dmg received for an attack-like ability using a flat AC bonus
    @param to_hit: to hit bonus
    @param dmg_dice: damage dice in a string form
    @param dmg_bonus: bonus to damage
    @param ac: target's AC
    @param ac_bonus: bonus to target's AC
    @return: mean damage decrement not accounting for critical failures (positive value)
    """
    return mean_dmg(to_hit, dmg_dice, dmg_bonus, ac, crit_range, is_resistant) - mean_dmg(to_hit, dmg_dice, dmg_bonus, ac + ac_bonus, crit_range, is_resistant)


@cache
def mean_dmg_bonus_increment_for_to_hit_bonus_dice(to_hit, dmg_dice, dmg_bonus, ac, bonus_dice_size):
    """
    Calculates the increase in mean dmg for an attack-like ability using a to-hit bonus die
    @param to_hit: to hit bonus
    @param dmg_dice: damage dice in a string form
    @param dmg_bonus: bonus to damage
    @param ac: target's AC
    @param bonus_dice_size:
    @return: mean damage increment not accounting for critical failures
    """
    return mean_dmg(to_hit + (1.0 + bonus_dice_size) / 2.0, dmg_dice, dmg_bonus, ac) - mean_dmg(to_hit, dmg_dice, dmg_bonus, ac)


def calculate_threat_in_mod(combatant, threat_radius, battle_map, roll_modifier, factory_flags):
    """
    Estimates the change in mean dmg from enemies within radius given a roll modifier assuming they'd all attack the combatant
    @param combatant: the potential receiver of the dmg
    @param threat_radius: radius within which enemies are to be considered
    @param battle_map:
    @param roll_modifier: the roll modifier to be considered (advantage or disadvantage)
    @param factory_flags: the kind of factory which is relevant for this calculation(e.g. attacks only or any direct threat...)
    @return: estimated change in dmg, negative for advantage, positive for disadvantage
    """
    potential_attackers = battle_map.get_enemies_within_hop_distance(combatant, threat_radius)
    incoming_threat_mod_acc = 0
    min_or_max = max if roll_modifier is RollModifier.ADVANTAGE else min
    for pa in potential_attackers:
        max_incoming_threat = 0
        for f in pa.action_factories:
            if factory_flags & f[1].flags:  # Checks for any overlap in flags
                max_incoming_threat = min_or_max(max_incoming_threat, f[1].calculate_threat_to_target_mod(battle_map, combatant, {
                    "roll_modifier": roll_modifier}))
        incoming_threat_mod_acc += max_incoming_threat

        max_incoming_threat = 0
        for f in pa.bonus_action_factories:
            if factory_flags & f[1].flags:  # Checks for any overlap in flags
                max_incoming_threat = min_or_max(max_incoming_threat, f[1].calculate_threat_to_target_mod(battle_map, combatant, {
                    "roll_modifier": roll_modifier}))
        incoming_threat_mod_acc += max_incoming_threat

        max_incoming_threat = 0
        for f in pa.haste_action_factories:
            if factory_flags & f[1].flags:  # Checks for any overlap in flags
                max_incoming_threat = min_or_max(max_incoming_threat, f[1].calculate_threat_to_target_mod(battle_map, combatant, {
                    "roll_modifier": roll_modifier}))
        incoming_threat_mod_acc += max_incoming_threat
    if roll_modifier is RollModifier.ADVANTAGE:
        assert incoming_threat_mod_acc >= 0
    else:
        assert incoming_threat_mod_acc <= 0
    return incoming_threat_mod_acc

def calculate_avg_threat_in(combatant, threat_radius, battle_map, factory_flags):
    """
    Estimates the mean dmg from enemies within radius they'd all attack the combatant
    @param combatant: the potential receiver of the dmg
    @param threat_radius: radius within which enemies are to be considered
    @param battle_map:
    @param factory_flags: the kind of factory which is relevant for this calculation(e.g. attacks only or any direct threat...)
    @return: estimated change in dmg, negative for advantage, positive for disadvantage
    """
    potential_attackers = battle_map.get_enemies_within_hop_distance(combatant, threat_radius)
    incoming_threat_acc = 0
    counter = 0
    for pa in potential_attackers:
        for f in pa.action_factories:
            if factory_flags & f[1].flags:  # Checks for any overlap in flags
                incoming_threat_acc += f[1].calculate_threat_to_target(battle_map, combatant)
                counter += 1

        for f in pa.bonus_action_factories:
            if factory_flags & f[1].flags:  # Checks for any overlap in flags
                incoming_threat_acc += f[1].calculate_threat_to_target(battle_map, combatant)
                counter += 1

        for f in pa.haste_action_factories:
            if factory_flags & f[1].flags:  # Checks for any overlap in flags
                incoming_threat_acc += f[1].calculate_threat_to_target(battle_map, combatant)
                counter += 1
    incoming_threat_acc /= counter
    return incoming_threat_acc

@cache
def mean_dmg_dc_attack(dc, dmg_dice, half_on_success, st_bonus, is_resistant=False):
    """
    Calculates mean damage of a DC-based ability
    @param dc: DC
    @param dmg_dice: dmg dice in string form
    @param half_on_success: True if half damage is received on a successful saving throw, False if zero
    @param st_bonus: respective saving throw bonus
    @return:
    """
    dice = parse_dmg_dice(dmg_dice)
    avg_dmg_die_roll = reduce(lambda acc, d: acc + d[0] * ((1.0 + d[1]) / 2.0), dice, 0)
    rv = randint(1, 21, st_bonus)
    p_fail = rv.cdf(dc - 1)
    fail_dmg = avg_dmg_die_roll * p_fail
    final_avg_dmg = fail_dmg + avg_dmg_die_roll / 2.0 * (1.0 - p_fail) if half_on_success else fail_dmg
    return final_avg_dmg if not is_resistant else final_avg_dmg / 2