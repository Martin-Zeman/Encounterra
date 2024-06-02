import os
import re
import time
import inspect
import logging

import numpy as np
import pytest

from ..actions.mcts import MCTS
from ..battle_map import Terrain
from ..logging.custom_logger import CustomLogger
from ..teams import Teams
from ..test.fixtures import test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, test_ogre, test_moon_druid, \
    teams, effect_tracker, battle_map, test_brown_bear, test_assassin_rogue, test_ghoul, test_hobgoblin, test_orc, \
    test_battle_master_fighter_lvl_5, test_zombie, test_owlbear, test_bullywug, test_oath_of_vengeance_paladin_lvl_5
from ..actions.action_selector import get_action

logger = logging.getLogger("Encounterra")
# @pytest.mark.mcts
# @pytest.mark.parametrize("iterations_param", [1000, 2000, 3000, 4000])
# def test_battlemaster_01(iterations_param, battle_map, teams, effect_tracker, test_battle_master_fighter_lvl_5, test_assassin_rogue,
#                               test_orc, test_bullywug, test_hobgoblin, test_oath_of_vengeance_paladin_lvl_5,
#                               test_owlbear, test_moon_druid, test_draconic_sorcerer_5lvl, test_zombie, test_ghoul):
#     """
#         Setting initial position [10  7] for Moon Druid 5th LVL (1)
#         Setting initial position [2 2] for Draconic Sorcerer 5th LVL (1)
#         Setting initial position [10  2] for Assassin Rogue 5th LVL (1)
#         Setting initial position [ 4 13] for Battlemaster Fighter 5th LVL (1)
#         Setting initial position [ 1 12] for Zombie (1)
#         Setting initial position [14 12] for Hobgoblin (1)
#         Setting initial position [10 12] for Oath of Vengeance Paladin 5th LVL (1)
#         Setting initial position [13  3] for Owlbear (1)
#         Setting initial position [5 5] for Ghoul (1)
#         Setting initial position [13  9] for Bullywug (1)
#         Setting initial position [2 6] for Orc (1)
#         14	..	..	..	..	..	..	..	..	..	..	..	..	..	..	..
#         13	..	..	..	..	B1	..	..	..	..	..	..	..	..	..	..
#         12	..	Z1	..	..	H1	..	..	..	..	..	O1	..	..	..	..
#         11	..	..	..	..	..	..	..	..	..	..	..	..	..	..	..
#         10	..	..	..	..	..	..	..	..	..	..	..	..	..	..	..
#          9	..	..	..	..	..	..	..	..	..	..	..	..	..	B1	..
#          8	..	..	..	..	..	..	..	..	..	..	..	..	..	..	..
#          7	..	..	..	..	..	..	..	..	..	..	M1	..	..	..	..
#          6	..	..	O1	..	..	..	..	..	..	..	..	..	..	..	..
#          5	..	..	..	..	..	G1	..	..	..	..	..	..	..	..	..
#          4	..	..	..	..	..	..	..	..	..	..	..	..	..	O1	O1
#          3	..	..	..	..	..	..	..	..	..	..	..	..	..	O1	O1
#          2	..	..	D1	..	..	..	..	..	..	..	A1	..	..	..	..
#          1	..	..	..	..	..	..	..	..	..	..	..	..	..	..	..
#          0	..	..	..	..	..	..	..	..	..	..	..	..	..	..	..
#             0	1	2	3	4	5	6	7	8	9	10	11	12	13	14
#     """
#     test_name = f"{inspect.stack()[0][3]}_{iterations_param}"
#     local_log_file_path = f"{test_name}.log"
#     if os.path.exists(local_log_file_path):
#         os.remove(local_log_file_path)
#     CustomLogger(logging.ERROR, True, local_log_file_path)
#     battle_map.set_effect_tracker(effect_tracker)
#     combatants = [test_battle_master_fighter_lvl_5, test_assassin_rogue, test_orc, test_bullywug, test_hobgoblin, test_oath_of_vengeance_paladin_lvl_5, test_owlbear, test_moon_druid, test_draconic_sorcerer_5lvl, test_zombie, test_ghoul]
#
#     teams.add_combatant_to_team(test_battle_master_fighter_lvl_5, Teams.Color.BLUE)
#     teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
#     teams.add_combatant_to_team(test_zombie, Teams.Color.BLUE)
#     teams.add_combatant_to_team(test_orc, Teams.Color.BLUE)
#     teams.add_combatant_to_team(test_ghoul, Teams.Color.BLUE)
#
#     teams.add_combatant_to_team(test_moon_druid, Teams.Color.RED)
#     # teams.add_combatant_to_team(test_hobgoblin, Teams.Color.RED)
#     teams.add_combatant_to_team(test_bullywug, Teams.Color.RED)
#     teams.add_combatant_to_team(test_owlbear, Teams.Color.RED)
#     teams.add_combatant_to_team(test_assassin_rogue, Teams.Color.RED)
#     teams.add_combatant_to_team(test_oath_of_vengeance_paladin_lvl_5, Teams.Color.RED)
#
#     # I'm trying to create a space where there's no danger zone
#     battle_map.set_combatant_coordinates(test_battle_master_fighter_lvl_5, np.array([4, 13]))
#     battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([2, 2]))
#     battle_map.set_combatant_coordinates(test_zombie, np.array([1, 12]))
#     battle_map.set_combatant_coordinates(test_orc, np.array([2, 6]))
#     battle_map.set_combatant_coordinates(test_ghoul, np.array([5, 5]))
#
#     battle_map.set_combatant_coordinates(test_moon_druid, np.array([10, 7]))
#     # battle_map.set_combatant_coordinates(test_hobgoblin, np.array([4, 12]))
#     battle_map.set_combatant_coordinates(test_bullywug, np.array([13, 9]))
#     battle_map.set_combatant_coordinates(test_owlbear, np.array([13, 3]))
#     battle_map.set_combatant_coordinates(test_assassin_rogue, np.array([10, 2]))
#     battle_map.set_combatant_coordinates(test_oath_of_vengeance_paladin_lvl_5, np.array([10, 12]))
#     for combatant in combatants:
#         combatant.curr_init = 0  # To prevent assassinate from crashing
#
#     battle_map.build_adjacency_matrix()
#     SAMPLE_SIZE = 200
#     PRINT_INTERVAL = 25
#
#     try:
#         logger.error("")
#         MCTS.ITERATIONS = iterations_param
#         success = 0
#         partial_success = 0
#         total_time = 0
#         for idx in range(SAMPLE_SIZE):
#             if idx % PRINT_INTERVAL == 0:
#                 logger.error(f"Iteration: {idx + 1}")
#                 logger.error(f"Success: {(100*success/(idx + 1)):.2f}%\t Partial Success: {(100*partial_success/(idx + 1)):.2f}%")
#             start_time = time.time()
#             _ = get_action(test_battle_master_fighter_lvl_5)
#             end_time = time.time()
#
#             duration = end_time - start_time
#             total_time += duration
#
#             best_sequence = test_battle_master_fighter_lvl_5.best_sequence
#             if [a for a in best_sequence if str(a).startswith('Menacing Greatsword')]:
#                 success += 1
#             elif [a for a in best_sequence if str(a).startswith('Greatsword')]:
#                 partial_success += 1
#             test_battle_master_fighter_lvl_5.action_plan.clear()
#         average_time = total_time / SAMPLE_SIZE
#         logger.error(f"Final results: Iterations: {iterations_param}\tSuccess: {(success/(SAMPLE_SIZE * 0.01)):.2f}%\t Partial Success: {(partial_success/(SAMPLE_SIZE * 0.01)):.2f}%")
#         logger.error(f"Average time per iteration: {average_time:.2f} seconds")
#     except Exception as e:
#         assert False, f"Raised an exception {e}"


@pytest.mark.mcts
@pytest.mark.parametrize("iterations_param", [1000, 2000, 3000, 4000])
def test_draconic_sorcerer_01(iterations_param, battle_map, teams, effect_tracker, test_battle_master_fighter_lvl_5, test_assassin_rogue,
                              test_orc, test_bullywug, test_hobgoblin, test_oath_of_vengeance_paladin_lvl_5,
                              test_owlbear, test_moon_druid, test_draconic_sorcerer_5lvl, test_zombie, test_ghoul):
    """
        Setting initial position [10  7] for Moon Druid 5th LVL (1)
        Setting initial position [2 2] for Draconic Sorcerer 5th LVL (1)
        Setting initial position [10  2] for Assassin Rogue 5th LVL (1)
        Setting initial position [ 4 13] for Battlemaster Fighter 5th LVL (1)
        Setting initial position [ 1 12] for Zombie (1)
        Setting initial position [14 12] for Hobgoblin (1)
        Setting initial position [10 12] for Oath of Vengeance Paladin 5th LVL (1)
        Setting initial position [13  3] for Owlbear (1)
        Setting initial position [5 5] for Ghoul (1)
        Setting initial position [13  9] for Bullywug (1)
        Setting initial position [2 6] for Orc (1)
        14	..	..	..	..	..	..	..	..	..	..	..	..	..	..	..
        13	..	..	..	..	B1	..	..	..	..	..	..	..	..	..	..
        12	..	Z1	..	..	H1	..	..	..	..	..	O1	..	..	..	..
        11	..	..	..	..	..	..	..	..	..	..	..	..	..	..	..
        10	..	..	..	..	..	..	..	..	..	..	..	..	..	..	..
         9	..	..	..	..	..	..	..	..	..	..	..	..	..	B1	..
         8	..	..	..	..	..	..	..	..	..	..	..	..	..	..	..
         7	..	..	..	..	..	..	..	..	..	..	M1	..	..	..	..
         6	..	..	O1	..	..	..	..	..	..	..	..	..	..	..	..
         5	..	..	..	..	..	G1	..	..	..	..	..	..	..	..	..
         4	..	..	..	..	..	..	..	..	..	..	..	..	..	O1	O1
         3	..	..	..	..	..	..	..	..	..	..	..	..	..	O1	O1
         2	..	..	D1	..	..	..	..	..	..	..	A1	..	..	..	..
         1	..	..	..	..	..	..	..	..	..	..	..	..	..	..	..
         0	..	..	..	..	..	..	..	..	..	..	..	..	..	..	..
            0	1	2	3	4	5	6	7	8	9	10	11	12	13	14
    """
    test_name = f"{inspect.stack()[0][3]}_{iterations_param}"
    local_log_file_path = f"{test_name}.log"
    if os.path.exists(local_log_file_path):
        os.remove(local_log_file_path)
    CustomLogger(logging.ERROR, True, local_log_file_path)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_battle_master_fighter_lvl_5, test_assassin_rogue, test_orc, test_bullywug, test_hobgoblin, test_oath_of_vengeance_paladin_lvl_5, test_owlbear, test_moon_druid, test_draconic_sorcerer_5lvl, test_zombie, test_ghoul]

    teams.add_combatant_to_team(test_battle_master_fighter_lvl_5, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_zombie, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_orc, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_ghoul, Teams.Color.BLUE)

    teams.add_combatant_to_team(test_moon_druid, Teams.Color.RED)
    # teams.add_combatant_to_team(test_hobgoblin, Teams.Color.RED)
    teams.add_combatant_to_team(test_bullywug, Teams.Color.RED)
    teams.add_combatant_to_team(test_owlbear, Teams.Color.RED)
    teams.add_combatant_to_team(test_assassin_rogue, Teams.Color.RED)
    teams.add_combatant_to_team(test_oath_of_vengeance_paladin_lvl_5, Teams.Color.RED)

    # I'm trying to create a space where there's no danger zone
    battle_map.set_combatant_coordinates(test_battle_master_fighter_lvl_5, np.array([4, 13]))
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([2, 2]))
    battle_map.set_combatant_coordinates(test_zombie, np.array([1, 12]))
    battle_map.set_combatant_coordinates(test_orc, np.array([2, 6]))
    battle_map.set_combatant_coordinates(test_ghoul, np.array([5, 5]))

    battle_map.set_combatant_coordinates(test_moon_druid, np.array([10, 7]))
    # battle_map.set_combatant_coordinates(test_hobgoblin, np.array([4, 12]))
    battle_map.set_combatant_coordinates(test_bullywug, np.array([13, 9]))
    battle_map.set_combatant_coordinates(test_owlbear, np.array([13, 3]))
    battle_map.set_combatant_coordinates(test_assassin_rogue, np.array([10, 2]))
    battle_map.set_combatant_coordinates(test_oath_of_vengeance_paladin_lvl_5, np.array([10, 12]))
    for combatant in combatants:
        combatant.curr_init = 0  # To prevent assassinate from crashing

    battle_map.build_adjacency_matrix()
    SAMPLE_SIZE = 200
    PRINT_INTERVAL = 25

    try:
        logger.error("")
        test_draconic_sorcerer_5lvl.action_plan_strategy.iterations = iterations_param
        success = 0
        total_time = 0
        for idx in range(SAMPLE_SIZE):
            if idx % PRINT_INTERVAL == 0:
                logger.error(f"Iteration: {idx + 1}")
                logger.error(f"Success: {(100*success/(idx + 1)):.2f}%")
            start_time = time.time()
            _ = get_action(test_draconic_sorcerer_5lvl)
            end_time = time.time()

            duration = end_time - start_time
            total_time += duration

            best_sequence = test_draconic_sorcerer_5lvl.best_sequence
            if [a for a in best_sequence if 'Fireball' in a] and [a for a in best_sequence if 'Quickened' in a]:
                success += 1
            test_draconic_sorcerer_5lvl.action_plan.clear()
        average_time = total_time / SAMPLE_SIZE
        logger.error(f"Final results: Iterations: {iterations_param}\tSuccess: {(success/(SAMPLE_SIZE * 0.01)):.2f}%")
        logger.error(f"Average time per iteration: {average_time:.2f} seconds")
    except Exception as e:
        assert False, f"Raised an exception {e}"


# @pytest.mark.mcts
# @pytest.mark.parametrize("iterations_param", [1000, 2000, 3000, 4000])
# def test_assassin_rogue_01(iterations_param, battle_map, teams, effect_tracker, test_battle_master_fighter_lvl_5, test_assassin_rogue,
#                               test_orc, test_bullywug, test_hobgoblin, test_oath_of_vengeance_paladin_lvl_5,
#                               test_owlbear, test_moon_druid, test_draconic_sorcerer_5lvl, test_zombie, test_ghoul):
#     """
#         Setting initial position [10  7] for Moon Druid 5th LVL (1)
#         Setting initial position [2 2] for Draconic Sorcerer 5th LVL (1)
#         Setting initial position [10  2] for Assassin Rogue 5th LVL (1)
#         Setting initial position [ 4 13] for Battlemaster Fighter 5th LVL (1)
#         Setting initial position [ 1 12] for Zombie (1)
#         Setting initial position [14 12] for Hobgoblin (1)
#         Setting initial position [10 12] for Oath of Vengeance Paladin 5th LVL (1)
#         Setting initial position [13  3] for Owlbear (1)
#         Setting initial position [5 5] for Ghoul (1)
#         Setting initial position [13  9] for Bullywug (1)
#         Setting initial position [2 6] for Orc (1)
#         14	..	..	..	..	..	..	..	..	..	..	..	..	..	..	..
#         13	..	..	..	..	B1	..	..	..	..	..	..	..	..	..	..
#         12	..	Z1	..	..	H1	..	..	..	..	..	O1	..	..	..	..
#         11	..	..	..	..	..	..	..	..	..	..	..	..	..	..	..
#         10	..	..	..	..	..	..	..	..	..	..	..	..	..	..	..
#          9	..	..	..	..	..	..	..	..	..	..	..	..	..	B1	..
#          8	..	..	..	..	..	..	..	..	..	..	..	..	..	..	..
#          7	..	..	..	..	..	..	..	..	..	..	M1	..	..	..	..
#          6	..	..	O1	..	..	..	..	..	..	..	..	..	..	..	..
#          5	..	..	..	..	..	G1	..	..	..	..	..	..	..	..	..
#          4	..	..	..	..	..	..	..	..	..	..	..	..	..	O1	O1
#          3	..	..	..	..	..	..	..	..	..	..	..	..	..	O1	O1
#          2	..	..	D1	..	..	..	..	..	..	..	A1	..	..	..	..
#          1	..	..	..	..	..	..	..	..	..	..	..	..	..	..	..
#          0	..	..	..	..	..	..	..	..	..	..	..	..	..	..	..
#             0	1	2	3	4	5	6	7	8	9	10	11	12	13	14
#     """
#     test_name = f"{inspect.stack()[0][3]}_{iterations_param}"
#     local_log_file_path = f"{test_name}.log"
#     if os.path.exists(local_log_file_path):
#         os.remove(local_log_file_path)
#     CustomLogger(logging.ERROR, True, local_log_file_path)
#     battle_map.set_effect_tracker(effect_tracker)
#     combatants = [test_battle_master_fighter_lvl_5, test_assassin_rogue, test_orc, test_bullywug, test_hobgoblin, test_oath_of_vengeance_paladin_lvl_5, test_owlbear, test_moon_druid, test_draconic_sorcerer_5lvl, test_zombie, test_ghoul]
#
#     battle_map.place_circular_element(np.array([7, 8]), Terrain.IMPASSABLE_TERRAIN, radius=1)
#     battle_map.place_circular_element(np.array([12, 6]), Terrain.IMPASSABLE_TERRAIN, radius=0)
#
#     teams.add_combatant_to_team(test_battle_master_fighter_lvl_5, Teams.Color.BLUE)
#     teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
#     teams.add_combatant_to_team(test_zombie, Teams.Color.BLUE)
#     teams.add_combatant_to_team(test_orc, Teams.Color.BLUE)
#     teams.add_combatant_to_team(test_ghoul, Teams.Color.BLUE)
#
#     teams.add_combatant_to_team(test_moon_druid, Teams.Color.RED)
#     # teams.add_combatant_to_team(test_hobgoblin, Teams.Color.RED)
#     teams.add_combatant_to_team(test_bullywug, Teams.Color.RED)
#     teams.add_combatant_to_team(test_owlbear, Teams.Color.RED)
#     teams.add_combatant_to_team(test_assassin_rogue, Teams.Color.RED)
#     teams.add_combatant_to_team(test_oath_of_vengeance_paladin_lvl_5, Teams.Color.RED)
#
#     # I'm trying to create a space where there's no danger zone
#     battle_map.set_combatant_coordinates(test_battle_master_fighter_lvl_5, np.array([4, 13]))
#     battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([2, 2]))
#     battle_map.set_combatant_coordinates(test_zombie, np.array([1, 12]))
#     battle_map.set_combatant_coordinates(test_orc, np.array([2, 6]))
#     battle_map.set_combatant_coordinates(test_ghoul, np.array([5, 5]))
#
#     battle_map.set_combatant_coordinates(test_moon_druid, np.array([10, 7]))
#     # battle_map.set_combatant_coordinates(test_hobgoblin, np.array([4, 12]))
#     battle_map.set_combatant_coordinates(test_bullywug, np.array([13, 9]))
#     battle_map.set_combatant_coordinates(test_owlbear, np.array([13, 3]))
#     battle_map.set_combatant_coordinates(test_assassin_rogue, np.array([10, 2]))
#     battle_map.set_combatant_coordinates(test_oath_of_vengeance_paladin_lvl_5, np.array([10, 12]))
#     for combatant in combatants:
#         combatant.curr_init = 0  # To prevent assassinate from crashing
#
#     battle_map.build_adjacency_matrix()
#     SAMPLE_SIZE = 200
#     PRINT_INTERVAL = 25
#
#     hide_action_pattern = re.compile(r"Cunning Hide of .* from (.+)")
#     shortbow_action_pattern = re.compile(r"Shortbow on (.+)")
#
#     try:
#         logger.error("")
#         MCTS.ITERATIONS = iterations_param
#         success = 0
#         total_time = 0
#         for idx in range(SAMPLE_SIZE):
#             if (idx + 1) % PRINT_INTERVAL == 0:
#                 logger.error(f"Iteration: {idx + 1}")
#                 logger.error(f"Success: {(100*success/(idx + 1)):.2f}%")
#             if test_assassin_rogue.action_plan:
#                 test_assassin_rogue.action_plan.clear()
#             start_time = time.time()
#             _ = get_action(test_assassin_rogue)
#             end_time = time.time()
#
#             duration = end_time - start_time
#             total_time += duration
#
#             best_sequence = test_assassin_rogue.best_sequence
#
#             contains_hide = any(act.startswith("Cunning Hide") for act in best_sequence)
#             if not contains_hide:
#                 continue
#             contains_shortbow = any(act.startswith("Shortbow") for act in best_sequence)
#             if not contains_shortbow:
#                 continue
#             contains_movement = any(act.startswith("m_(") for act in best_sequence)
#             if not contains_movement:
#                 continue
#             hide_precedes_shortbow = next(i for i, act in enumerate(best_sequence) if act.startswith("Cunning Hide")) < next(i for i, act in enumerate(best_sequence) if act.startswith("Shortbow"))
#             if not hide_precedes_shortbow:
#                 continue
#             hide_target = next(hide_action_pattern.match(act).group(1) for act in best_sequence if hide_action_pattern.match(act))
#             shortbow_target = next(shortbow_action_pattern.match(act).group(1) for act in best_sequence if shortbow_action_pattern.match(act))
#             same_target = hide_target == shortbow_target
#             if not same_target:
#                 continue
#             success += 1
#         average_time = total_time / SAMPLE_SIZE
#         logger.error(f"Final results: Iterations: {iterations_param}\tSuccess: {(success/(SAMPLE_SIZE * 0.01)):.2f}%")
#         logger.error(f"Average time per iteration: {average_time:.2f} seconds")
#     except Exception as e:
#         assert False, f"Raised an exception {e}"


# @pytest.mark.mcts
# @pytest.mark.parametrize("iterations_param", [1000, 2000, 3000, 4000])
# def test_assassin_rogue_02(iterations_param, battle_map, teams, effect_tracker, test_assassin_rogue, test_bugbear, test_ogre, test_goblin, test_brown_bear):
#     """
#     14	..	..	..	..	..	..	..	..	..	..	..	..	..	..	..
#     13	..	..	..	..	..	..	..	..	..	..	..	..	..	..	..
#     12	..	..	..	..	..	..	..	..	..	..	..	XX	..	..	..
#     11	..	..	XX	..	..	G1	..	..	..	..	..	..	..	..	..
#     10	..	..	..	..	..	..	..	..	..	..	..	..	..	..	..
#      9	..	..	..	..	..	XX	XX	XX	..	..	..	..	..	..	..
#      8	..	..	..	..	..	XX	XX	XX	..	..	..	..	B1	..	..
#      7	..	..	..	..	..	XX	XX	XX	..	..	..	..	..	..	..
#      6	..	..	..	..	..	..	..	..	..	..	..	..	..	..	..
#      5	..	A1	..	..	..	..	..	..	..	..	..	..	..	..	..
#      4	..	..	..	..	..	..	..	..	..	..	..	..	..	..	..
#      3	..	..	..	..	..	..	..	..	..	..	..	..	..	..	..
#      2	..	..	O1	O1	..	..	..	..	XX	..	..	..	..	..	..
#      1	..	..	O1	O1	..	..	..	..	..	..	..	..	..	Ba	Ba
#      0	..	..	..	..	..	..	..	..	..	..	..	..	..	Ba	Ba
#         0	1	2	3	4	5	6	7	8	9	10	11	12	13	14
#     """
#     test_name = f"{inspect.stack()[0][3]}_{iterations_param}"
#     local_log_file_path = f"{test_name}.log"
#     if os.path.exists(local_log_file_path):
#         os.remove(local_log_file_path)
#     CustomLogger(logging.ERROR, True, local_log_file_path)
#     battle_map.set_effect_tracker(effect_tracker)
#     battle_map.place_circular_element(np.array([6, 8]), Terrain.IMPASSABLE_TERRAIN, radius=1)
#     battle_map.place_circular_element(np.array([8, 2]), Terrain.IMPASSABLE_TERRAIN, radius=0)
#     battle_map.place_circular_element(np.array([2, 11]), Terrain.IMPASSABLE_TERRAIN, radius=0)
#     battle_map.place_circular_element(np.array([11, 12]), Terrain.IMPASSABLE_TERRAIN, radius=0)
#     combatants = [test_assassin_rogue, test_bugbear, test_ogre, test_goblin, test_brown_bear]
#     teams.add_combatant_to_team(test_assassin_rogue, Teams.Color.BLUE)
#     teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
#     teams.add_combatant_to_team(test_ogre, Teams.Color.RED)
#     teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
#     teams.add_combatant_to_team(test_brown_bear, Teams.Color.RED)
#     battle_map.set_combatant_coordinates(test_assassin_rogue, np.array([1, 5]))
#     battle_map.set_combatant_coordinates(test_bugbear, np.array([12, 8]))
#     battle_map.set_combatant_coordinates(test_ogre, np.array([2, 1]))
#     battle_map.set_combatant_coordinates(test_goblin, np.array([5, 11]))
#     battle_map.set_combatant_coordinates(test_brown_bear, np.array([13, 0]))
#     battle_map.build_adjacency_matrix()
#     for combatant in combatants:
#         combatant.curr_init = 0  # To prevent assassinate from crashing
#
#     SAMPLE_SIZE = 200
#     PRINT_INTERVAL = 25
#
#     hide_action_pattern = re.compile(r"Cunning Hide of .* from (.+)")
#     shortbow_action_pattern = re.compile(r"Shortbow on (.+)")
#
#     try:
#         logger.error("")
#         MCTS.ITERATIONS = iterations_param
#         success = 0
#         total_time = 0
#         for idx in range(SAMPLE_SIZE):
#             if (idx + 1) % PRINT_INTERVAL == 0:
#                 logger.error(f"Iteration: {idx + 1}")
#                 logger.error(f"Success: {(100*success/(idx + 1)):.2f}%")
#             if test_assassin_rogue.action_plan:
#                 test_assassin_rogue.action_plan.clear()
#             start_time = time.time()
#             _ = get_action(test_assassin_rogue)
#             end_time = time.time()
#
#             duration = end_time - start_time
#             total_time += duration
#
#             best_sequence = test_assassin_rogue.best_sequence
#
#             contains_hide = any(act.startswith("Cunning Hide") for act in best_sequence)
#             if not contains_hide:
#                 continue
#             contains_shortbow = any(act.startswith("Shortbow") for act in best_sequence)
#             if not contains_shortbow:
#                 continue
#             contains_movement = any(act.startswith("m_(") for act in best_sequence)
#             if not contains_movement:
#                 continue
#             hide_precedes_shortbow = next(i for i, act in enumerate(best_sequence) if act.startswith("Cunning Hide")) < next(i for i, act in enumerate(best_sequence) if act.startswith("Shortbow"))
#             if not hide_precedes_shortbow:
#                 continue
#             hide_target = next(hide_action_pattern.match(act).group(1) for act in best_sequence if hide_action_pattern.match(act))
#             shortbow_target = next(shortbow_action_pattern.match(act).group(1) for act in best_sequence if shortbow_action_pattern.match(act))
#             same_target = hide_target == shortbow_target
#             if not same_target:
#                 continue
#             success += 1
#         average_time = total_time / SAMPLE_SIZE
#         logger.error(f"Final results: Iterations: {iterations_param}\tSuccess: {(success/(SAMPLE_SIZE * 0.01)):.2f}%")
#         logger.error(f"Average time per iteration: {average_time:.2f} seconds")
#     except Exception as e:
#         assert False, f"Raised an exception {e}"
