import time
import os

import pytest
import pickle

from simulator.battle_map import Map
from simulator.combatants.assassin_rogue_3lvl import AssassinRogue3Lvl
from simulator.combatants.battlemaster_fighter_3lvl import BattlemasterFighter3Lvl
from simulator.combatants.druid_1lvl import Druid1Lvl
from simulator.combatants.fighter_1lvl import Fighter1Lvl
from simulator.combatants.fighter_2lvl import Fighter2Lvl
from simulator.logging.custom_logger import CustomLogger
from simulator.misc import Statistics
from simulator.session import Session
from simulator.combatants.draconic_sorcerer_5lvl import DraconicSorcerer5Lvl
from simulator.combatants.draconic_sorcerer_3lvl import DraconicSorcerer3Lvl
from simulator.combatants.moon_druid_5lvl import MoonDruid5Lvl
from simulator.teams import Teams
import logging

logger = logging.getLogger("Encounterra")

SERIALIZE_DIR = 'serialized_objects'


def assert_keywords_in_log(file_path, keywords):
    """Check if all provided keywords are present in the log file.

    Args:
        file_path (str): Path to the log file.
        keywords (list of str): Keywords to search for in the log file.

    Raises:
        AssertionError: If any keyword is not found in the log file.
    """
    with open(file_path, 'r') as f:
        log_content = f.read()

    missing_keywords = [keyword for keyword in keywords if keyword not in log_content]
    if missing_keywords:
        assert False, f"The following keywords were not found in the log: {missing_keywords}"


def assert_victories_with_tolerance(results, team_color, expected_percentage, tolerance_percentage):
    """Assert that the victory percentage for a team is within a certain tolerance.

    Args:
        results (dict): The results dictionary from the simulation.
        team_color (Teams.Color): The team color to check the victories for.
        expected_percentage (float): The expected victory percentage (0-100).
        tolerance_percentage (float): The allowed tolerance in the victory percentage (0-100).

    Raises:
        AssertionError: If the victory percentage is outside the expected range.
    """
    total_simulations = sum(results[team_color][Statistics.VICTORIES] for team_color in results)
    if total_simulations == 0:
        raise ValueError("Total number of simulations is zero, cannot calculate victory percentage.")

    actual_victories = results[team_color][Statistics.VICTORIES]
    actual_percentage = (actual_victories / total_simulations) * 100
    min_percentage = expected_percentage - tolerance_percentage
    max_percentage = expected_percentage + tolerance_percentage
    assert min_percentage <= actual_percentage <= max_percentage, (
        f"Expected victory percentage for team {team_color} to be between {min_percentage}% and {max_percentage}%, "
        f"but got {actual_percentage}%."
    )

@pytest.mark.slow
def test_matchup_1():
    log_path = "/tmp/test_matchup_1_log.txt"
    if os.path.exists(log_path):
        os.remove(log_path)
    CustomLogger(logging.INFO, False, log_path)
    blue_team = [DraconicSorcerer5Lvl, AssassinRogue3Lvl]
    red_team = [MoonDruid5Lvl, DraconicSorcerer3Lvl]
    logger.info(f"Starting a statistical test with:")
    logger.info(f"Blue team: {[str(c) for c in blue_team]}")
    logger.info(f"Red team: {[str(c) for c in red_team]}")
    keywords = [
        "Moon Druid 5th LVL (1) wildshapes into",
        "Assassin Rogue 3rd LVL (1) attempts to hide",
        "Activating Sneak Attack",
        "Draconic Sorcerer 3rd LVL (1) casts Quickened"
        "Draconic Sorcerer 5th LVL (1) casts Quickened"
    ]

    Map.reset_singleton()
    session = Session()

    for combatant in blue_team:
        session.add_combatant(combatant, Teams.Color.BLUE)
    for combatant in red_team:
        session.add_combatant(combatant, Teams.Color.RED)

    session.set_num_simulations(20)
    session.place_terrain_and_obstacles(Session.MapType.OBSTACLES_AND_DIFFICULT_TERRAIN.value)
    try:
        results = session.simulate(parallel=False)
        assert_keywords_in_log(log_path, keywords)
        assert_victories_with_tolerance(results, Teams.Color.BLUE, 90, 10)
        assert_victories_with_tolerance(results, Teams.Color.RED, 10, 10)
        os.remove(log_path)
    except AssertionError:
        raise
    except Exception as e:
        timestamp = int(time.time())
        with open(os.path.join(SERIALIZE_DIR, f'battle_map_data_{timestamp}.pkl'), 'wb') as f:
            pickle.dump(Map.serialize_data(), f)
        with open(os.path.join(SERIALIZE_DIR, f'session_{timestamp}.pkl'), 'wb') as f:
            pickle.dump(session.serialize_data(), f)
        with open(os.path.join(SERIALIZE_DIR, f'exception_{timestamp}.txt'), 'w') as f:
            f.write(f"Fuzzy test with Blue team {blue_team} and Red team {red_team} raised an exception:\n{e}")
        os.remove(log_path)

        assert False, f"Fuzzy test with Blue team {blue_team} and Red team {red_team} raised an exception {e}"


@pytest.mark.slow
def test_matchup_2():
    log_path = "/tmp/test_matchup_2_log.txt"
    if os.path.exists(log_path):
        os.remove(log_path)
    CustomLogger(logging.INFO, False, log_path)
    blue_team = [Druid1Lvl, Fighter1Lvl]
    red_team = [Druid1Lvl, Fighter1Lvl]
    logger.info(f"Starting a statistical test with:")
    logger.info(f"Blue team: {[str(c) for c in blue_team]}")
    logger.info(f"Red team: {[str(c) for c in red_team]}")
    keywords = [
        "Druid 1st LVL (1) casts Thunderwave",
        "Druid 1st LVL (2) casts Thunderwave",
        "Fighter 1st LVL (1) attacks Druid 1st LVL (2) with Greatsword",
        "Fighter 1st LVL (2) attacks Druid 1st LVL (1) with Greatsword",
        "Fighter 1st LVL (1) attacks Fighter 1st LVL (2) with Greatsword",
        "Fighter 1st LVL (2) attacks Fighter 1st LVL (1) with Greatsword",
        "Druid 1st LVL (1) casts Faerie Fire",
        "Druid 1st LVL (2) casts Faerie Fire",
        "Fighter 1st LVL (1) uses Second Wind",
        "Fighter 1st LVL (2) uses Second Wind",
        "Druid 1st LVL (1) casts Shillelagh on Quarterstaff",
        "Druid 1st LVL (2) casts Shillelagh on Quarterstaff"
    ]

    Map.reset_singleton()
    session = Session()

    for combatant in blue_team:
        session.add_combatant(combatant, Teams.Color.BLUE)
    for combatant in red_team:
        session.add_combatant(combatant, Teams.Color.RED)

    session.set_num_simulations(50)
    session.place_terrain_and_obstacles(Session.MapType.OBSTACLES_AND_DIFFICULT_TERRAIN.value)
    try:
        results = session.simulate(parallel=False)
        assert_keywords_in_log(log_path, keywords)
        assert_victories_with_tolerance(results, Teams.Color.BLUE, 50, 15)
        assert_victories_with_tolerance(results, Teams.Color.RED, 50, 15)
        os.remove(log_path)
    except AssertionError:
        raise
    except Exception as e:
        timestamp = int(time.time())
        with open(os.path.join(SERIALIZE_DIR, f'battle_map_data_{timestamp}.pkl'), 'wb') as f:
            pickle.dump(Map.serialize_data(), f)
        with open(os.path.join(SERIALIZE_DIR, f'session_{timestamp}.pkl'), 'wb') as f:
            pickle.dump(session.serialize_data(), f)
        with open(os.path.join(SERIALIZE_DIR, f'exception_{timestamp}.txt'), 'w') as f:
            f.write(f"Fuzzy test with Blue team {blue_team} and Red team {red_team} raised an exception:\n{e}")
        os.remove(log_path)

        assert False, f"Fuzzy test with Blue team {blue_team} and Red team {red_team} raised an exception {e}"


@pytest.mark.slow
def test_matchup_3():
    log_path = "/tmp/test_matchup_3_log.txt"
    if os.path.exists(log_path):
        os.remove(log_path)
    CustomLogger(logging.INFO, False, log_path)
    blue_team = [Fighter2Lvl, Fighter1Lvl]
    red_team = [BattlemasterFighter3Lvl]
    logger.info(f"Starting a statistical test with:")
    logger.info(f"Blue team: {[str(c) for c in blue_team]}")
    logger.info(f"Red team: {[str(c) for c in red_team]}")
    keywords = [
        "Fighter 1st LVL (1) attacks Battlemaster Fighter 3rd LVL (1) with Greatsword",
        "Fighter 2nd LVL (1) attacks Battlemaster Fighter 3rd LVL (1) with Greatsword",
        "Battlemaster Fighter 3rd LVL (1) attacks Fighter 2nd LVL (1) with Menacing Greatsword",
        "Battlemaster Fighter 3rd LVL (1) attacks Fighter 1st LVL (1) with Menacing Greatsword",
        "Battlemaster Fighter 3rd LVL (1) attacks Fighter 1st LVL (1) with Riposte Greatsword",
        "Battlemaster Fighter 3rd LVL (1) attacks Fighter 2nd LVL (1) with Riposte Greatsword",
        "Battlemaster Fighter 3rd LVL (1) attacks Fighter 1st LVL (1) with Menacing Handaxe at disadvantage",
        "Battlemaster Fighter 3rd LVL (1) attacks Fighter 2nd LVL (1) with Menacing Handaxe at disadvantage",
        "Fighter 2nd LVL (1) is frightened",
        "Fighter 1st LVL (1) is frightened",
    ]

    Map.reset_singleton()
    session = Session()

    for combatant in blue_team:
        session.add_combatant(combatant, Teams.Color.BLUE)
    for combatant in red_team:
        session.add_combatant(combatant, Teams.Color.RED)

    session.set_num_simulations(50)
    session.place_terrain_and_obstacles(Session.MapType.OBSTACLES_AND_DIFFICULT_TERRAIN.value)
    try:
        results = session.simulate(parallel=False)
        assert_keywords_in_log(log_path, keywords)
        assert_victories_with_tolerance(results, Teams.Color.BLUE, 26, 15)
        assert_victories_with_tolerance(results, Teams.Color.RED, 74, 15)
        os.remove(log_path)
    except AssertionError:
        raise
    except Exception as e:
        timestamp = int(time.time())
        with open(os.path.join(SERIALIZE_DIR, f'battle_map_data_{timestamp}.pkl'), 'wb') as f:
            pickle.dump(Map.serialize_data(), f)
        with open(os.path.join(SERIALIZE_DIR, f'session_{timestamp}.pkl'), 'wb') as f:
            pickle.dump(session.serialize_data(), f)
        with open(os.path.join(SERIALIZE_DIR, f'exception_{timestamp}.txt'), 'w') as f:
            f.write(f"Fuzzy test with Blue team {blue_team} and Red team {red_team} raised an exception:\n{e}")
        os.remove(log_path)

        assert False, f"Fuzzy test with Blue team {blue_team} and Red team {red_team} raised an exception {e}"
