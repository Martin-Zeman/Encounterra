import copy
import sys
import time
from functools import cache, reduce

import numpy as np
from cachetools import cached
from cachetools.keys import hashkey
from scipy.stats import randint
from toposort import toposort_flatten
from transitions import Machine
from transitions.extensions import GraphMachine

from simulator.actions.actoid import FactoryFlags
from simulator.utils.state_machine_template import StateMachineTemplate
from simulator.misc import parse_dmg_dice, reconstruct_path_through_dag
from simulator.spells.misty_step import MistyStepFactory
from simulator.utils.roll_modifiers import RollModifier


DZ_CONSTANT = 0.33

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
            if factory_flags & f[1].flags and not f[1].flags & FactoryFlags.USES_CALCULATE_THREAT_IN_MOD:  # Checks for any overlap in flags
                max_incoming_threat = min_or_max(max_incoming_threat, f[1].calculate_threat_to_target_delta(battle_map, combatant, {
                    "roll_modifier": roll_modifier}))
        incoming_threat_mod_acc += max_incoming_threat

        max_incoming_threat = 0
        for f in pa.bonus_action_factories:
            if factory_flags & f[1].flags and not f[1].flags & FactoryFlags.USES_CALCULATE_THREAT_IN_MOD:  # Checks for any overlap in flags
                max_incoming_threat = min_or_max(max_incoming_threat, f[1].calculate_threat_to_target_delta(battle_map, combatant, {
                    "roll_modifier": roll_modifier}))
        incoming_threat_mod_acc += max_incoming_threat

        max_incoming_threat = 0
        for f in pa.haste_action_factories:
            if factory_flags & f[1].flags and not f[1].flags & FactoryFlags.USES_CALCULATE_THREAT_IN_MOD:  # Checks for any overlap in flags
                max_incoming_threat = min_or_max(max_incoming_threat, f[1].calculate_threat_to_target_delta(battle_map, combatant, {
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
def get_saving_throw_success_prob(dc, st_bonus):
    """
    Calculates the probability of a successful saving throw given the DC and the ST bonus
    @param dc: DC
    @param st_bonus: respective saving throw bonus
    @return:
    """
    rv = randint(1, 21, st_bonus)
    p_fail = rv.cdf(dc - 1)
    return 1 - p_fail

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
    acc = reduce(lambda acc, e: acc + (e.danger_zone_attack[1].calculate_threat_to_target(battle_map, combatant) * DZ_CONSTANT if
        battle_map.get_hop_distance(e, coords) <= e.speed + e.danger_zone_attack[1].range else 0), enemies, 0)
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
            t = effect.threat_on_start_of_turn(battle_map, combatant)
            assert t >= 0
            threat_acc += t
            t = effect.threat_on_end_of_turn(battle_map, combatant)
            assert t >= 0
            threat_acc += t
    dzt = get_danger_zone_threat(battle_map, coords, combatant)
    assert dzt >= 0
    threat_acc += dzt
    return threat_acc


@cached(cache={}, key=lambda curr_coords_data, increment, battle_map, combatant, effect_to_coords, disengaged, dodged: hashkey((tuple(curr_coords_data[0]), tuple(increment), disengaged, dodged)))
def get_aoe_and_aoo_threat_for_increment(curr_coords_data, increment, battle_map, combatant, effect_to_coords, disengaged=False, dodged=False):
    """
    A helper caching function which accumulates threats from AoE and AoO along a path.
    Caution: get_aoe_and_aoo_threat_for_increment uses a global cache which may need to be cleared!
    :param curr_coords_data: current coordinate as np.array
    :param increment: the current coordinate increment
    :param battle_map:
    :param combatant: the moving combatant
    :param effect_to_coords: mapping of AoE effects to their coordinates
    :param disengaged: If True then don't include the AoOs
    :return: accumulated threat (negative)
    """
    roll_modifier = RollModifier.DISADVANTAGE if dodged else RollModifier.STRAIGHT
    threat_acc = 0
    with battle_map.as_if_combatant_position(combatant, curr_coords_data[0]):
        # account for AoO
        if not disengaged:
            enemies = battle_map.get_aoo_eligible_combatants(combatant, increment)
            for e in enemies:
                t = e.aoo_factory[1].calculate_threat_to_target(battle_map, combatant, roll_modifier=roll_modifier)
                assert t >= 0
                threat_acc -= t

        # account for AoE
        for effect, affected_coords in effect_to_coords.items():
            pre_increment_dist = battle_map.get_hop_distance(curr_coords_data, affected_coords)
            post_increment_dist = battle_map.get_hop_distance(curr_coords_data + increment, affected_coords)
            if pre_increment_dist == 1 and post_increment_dist == 0:
                t = effect.threat_on_enter(battle_map, combatant)
                assert t >= 0
                threat_acc -= t
            elif pre_increment_dist == 0 and post_increment_dist == 0:
                t = effect.threat_on_move_within(battle_map, combatant)
                assert t >= 0
                threat_acc -= t
    return threat_acc


def accumulate_threat_along_path(battle_map, path, combatant, effect_to_coords, disengaged=False, dodged=False):
    """
    Accumulates threats along a path. Also takes into account the threat associated with ending/starting a turn
    at the final destination. Caution: get_aoe_and_aoo_threat_for_increment uses a global cache which may need to be cleared!
    :param battle_map:
    :param path: path as a sequence of np.array coordinates
    :param combatant: the moving combatant
    :param effect_to_coords: mapping of AoE effects to their coordinates
    :param disengaged: If True then don't include the AoOs
    :param dodged: If True then attacks at the moving combatant are calculated at a disadvantage
    :return: accumulated threat (negative)
    """
    threat_acc = 0
    curr_coords = battle_map.get_combatant_position(combatant)
    curr_coords_data = copy.copy(curr_coords.get())  # TODO shallow copy should be enough here
    for increment in path:
        t = get_aoe_and_aoo_threat_for_increment(curr_coords_data, increment, battle_map, combatant, effect_to_coords, disengaged, dodged)
        assert t <= 0
        threat_acc += t
        curr_coords_data += increment
    # account for the final destination
    t = get_threat_for_staying_at_coord(battle_map, curr_coords_data if path else curr_coords.get(), combatant)
    assert t >= 0
    threat_acc -= t
    return threat_acc

def calc_threat_for_path_with_misty_step(battle_map, path, combatant, effect_to_coords):
    """
    Accumulates threats along a path. Also takes into account the threat associated with ending/starting a turn
    at the final destination. Caution: get_aoe_and_aoo_threat_for_increment uses a global cache which may need to be cleared!
    :param battle_map:
    :param path: path as a sequence of np.array coordinates
    :param combatant: the moving combatant
    :param effect_to_coords: mapping of AoE effects to their coordinates
    :param disengaged: If True then don't include the AoOs
    :return: accumulated threat (negative)
    """
    # TODO Make it prefer
    # class Dummy(object):
    #     pass
    threat_acc = 0
    max_threat_path = None

    # First build the Misty Step DAG
    curr_coords = battle_map.get_combatant_position(combatant)
    if path:
        # We build a DAG with two branches where one branch represents moving before using Misty Step and the other after
        # The only transitions between the branches represent Misty Step itself which can be taken at different points of the path
        curr_coords_data = copy.copy(curr_coords.get())  # TODO shallow copy should be enough here
        coords = [curr_coords.get()[0]]
        initial_state_name = str(tuple(curr_coords_data[0]))
        states = [initial_state_name]
        transitions = []
        previous_state = states[-1]
        previous_ms_state = states[-1]
        transition_to_threat = dict()
        for increment in path:
            curr_threat = get_aoe_and_aoo_threat_for_increment(curr_coords_data, increment, battle_map, combatant, effect_to_coords, False, False)
            curr_coords_data += increment
            coords.append(copy.copy(curr_coords_data[0]))
            new_state_name = str(tuple(curr_coords_data[0]))
            new_ms_state_name = "ms_" + new_state_name
            states.append(new_state_name)
            states.append(new_ms_state_name)
            transition_name = 'm_to_' + new_state_name
            ms_transition_name = 'm_to_' + new_ms_state_name
            transitions.append([transition_name, previous_state, new_state_name])
            transitions.append([ms_transition_name, previous_ms_state, new_ms_state_name])
            transition_to_threat[transition_name] = curr_threat
            transition_to_threat[ms_transition_name] = curr_threat
            previous_state = new_state_name
            previous_ms_state = new_ms_state_name
        ms_dag = StateMachineTemplate()
        ms_dag.states = states
        ms_dag.initial = initial_state_name
        ms_dag.dependencies = dict()
        for t in transitions:
            ms_dag.add_transition(t[0], t[1], t[2])
        # dummy = Dummy()
        # graph_ms_dag = GraphMachine(dummy, states=ms_dag.states, transitions=transitions, initial=initial_state_name)
        for i in range(0, len(coords) - 1):
            for j in range(i + 1, len(coords)):
                if np.linalg.norm(coords[i] - coords[j]) <= MistyStepFactory.range:
                    dest_name = "ms_" + str(tuple(coords[j]))
                    ms_dag.add_transition('ms_to_' + dest_name, str(tuple(coords[i])), dest_name)
                    # graph_ms_dag.add_transition('ms_to_' + dest_name, str(tuple(coords[i])), dest_name)

        # Then sort the states topologically and find the longest path
        sorted_states = toposort_flatten(ms_dag.dependencies)
        assert "ms_" in sorted_states[-1]  # TODO remove this later
        MINUS_INF = -sys.maxsize - 1
        threat = dict.fromkeys(sorted_states, MINUS_INF)
        threat[sorted_states[0]] = 0
        max_threat_backwards_transition = {sorted_states[0]: None}  # it's guaranteed that the first state is the initial coord
        for state in sorted_states:
            try:
                for transition_name, target_state in ms_dag.forward_transitions[state]:
                    threat_acc = ((0 if transition_name.startswith("ms") else transition_to_threat[transition_name]) + threat[state]) if threat[state] > MINUS_INF else 0
                    if threat_acc > threat[target_state]:
                        threat[target_state] = threat_acc
                        max_threat_backwards_transition[target_state] = (transition_name, state)
            except KeyError:
                pass  # Ok, for the last state in each branch as they are leaves and have no out edges

        max_threat_path = reconstruct_path_through_dag(sorted_states[-1], sorted_states[0], max_threat_backwards_transition)
        threat_acc += threat[states[-1]]  # the last ms state was added last which represents the longest (best) path
        # graph_ms_dag.get_graph().draw('misty_step_dag.png', prog='dot')
    # account for the final destination
    threat_acc -= get_threat_for_staying_at_coord(battle_map, curr_coords_data if path else curr_coords.get(), combatant)
    return threat_acc, max_threat_path

