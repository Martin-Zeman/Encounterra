import copy
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
            try:
                if factory_flags & f[1].flags:  # Checks for any overlap in flags
                    max_incoming_threat = min_or_max(max_incoming_threat, f[1].calculate_threat_to_target_mod(battle_map, combatant, {
                        "roll_modifier": roll_modifier}))
            except AttributeError:
                print("FIXME")
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

def get_danger_zone_threat(battle_map, coords, combatant):
    """
    Adds potential threat projected by the virtue of being near an enemy. It adds up all the projected threat for all
    enemies within their projection range.
    move.
    :param battle_map:
    :param coords: as np.array of size nx2 where n is the number of coords the combatant takes up
    :param combatant:
    :return: danger zone threat (positive)
    """
    enemies = battle_map.get_enemies(combatant)
    acc = reduce(lambda acc, e: acc + e.danger_zone_attack[1].calculate_threat_to_target(battle_map, combatant) if
        battle_map.get_hop_distance(e, coords) <= e.speed + e.danger_zone_attack[1].range else 0, enemies, 0)
    return acc

def get_threat_for_staying_at_coord(battle_map, coords, combatant):
    """
    Estimates te threat associated with staying at a coordinate. This is really an estimate since the character may still
    move.
    :param battle_map:
    :param coords: as np.array of size nx2 where n is the number of coords the combatant takes up
    :param combatant:
    :return: estimated threat (positive)
    """
    threat_acc = 0
    effect_to_coords = {e: e.get_affected_coords(battle_map) for e in battle_map.effect_tracker.get_aoe_effects()}
    for effect, affected_coords in effect_to_coords.items():
        if battle_map.get_hop_distance(affected_coords, coords) == 0:
            threat_acc += effect.threat_on_start_of_turn(battle_map, combatant)
            threat_acc += effect.threat_on_end_of_turn(battle_map, combatant)
    threat_acc += get_danger_zone_threat(battle_map, coords, combatant)
    return threat_acc


def accumulate_threat_along_path(battle_map, path, combatant, disengaged=False):
    """
    Accumulates threats along a path. Also takes into account the threat associated with ending/starting a turn
    at the final destination.
    :param battle_map:
    :param path: path as a sequence of np.array coordinates
    :param combatant: the moving combatant
    :param disengaged: If True then don't include the AoOs
    :return: accumulated threat (negative)
    """
    # TODO Add test where the character runs out of the danger zone
    threat_acc = 0
    curr_coords = copy.deepcopy(battle_map.get_combatant_position(combatant))
    effect_to_coords = {e: e.get_affected_coords(battle_map) for e in battle_map.effect_tracker.get_aoe_effects()}

    try:
        for increment in path:
            curr_coords_data = curr_coords.get()
            with battle_map.as_if_combatant_position(combatant, curr_coords_data[0]):
                # account for AoO
                if not disengaged:
                    enemies = battle_map.get_aoo_eligible_combatants(combatant, increment)
                    for e in enemies:
                        threat_acc -= e.aoo_factory[1].calculate_threat_to_target(battle_map, combatant)

                # account for AoE
                for effect, affected_coords in effect_to_coords.items():
                    pre_increment_dist = battle_map.get_hop_distance(curr_coords_data, affected_coords)
                    post_increment_dist = battle_map.get_hop_distance(curr_coords_data + increment, affected_coords)
                    if pre_increment_dist == 1 and post_increment_dist == 0:
                        threat_acc -= effect.threat_on_enter(battle_map, combatant)
                    elif pre_increment_dist == 0 and post_increment_dist == 0:
                        threat_acc -= effect.threat_on_move_within(battle_map, combatant)
            curr_coords_data += increment
        # account for the final destination
        threat_acc -= get_threat_for_staying_at_coord(battle_map, curr_coords_data if path else curr_coords.get(), combatant)
    except TypeError as e:
        print("FIXME")
    return threat_acc
