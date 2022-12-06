from simulator.map import *
from simulator.round_manager import *
from simulator.teams import Teams
from simulator.characters.rena import Rena
from simulator.characters.cyanwrath import Cyanwrath
import numpy as np
import logging
import sys
from simulator.logging.log_formatter import LogFormatter
import random

if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    stdout_handler.setFormatter(LogFormatter())
    logger.addHandler(stdout_handler)

    cyanwrath = Cyanwrath()
    rena = Rena()
    combatants = [cyanwrath, rena]
    teams = Teams()
    teams.add_char_to_team(cyanwrath, "Blue")
    teams.add_char_to_team(rena, "Red")
    battle_map = Map(15, teams)
    battle_map.set_character_coordinates(cyanwrath, np.array([random.randint(0, 14), random.randint(8, 14)]))
    battle_map.set_character_coordinates(rena, np.array([random.randint(0, 14), random.randint(0, 6)]))
    combat_manager = CombatManager(combatants, teams, battle_map)
    round_manager = RoundManager(combatants, teams, battle_map, combat_manager)
    cyanwrath.set_round_manager(round_manager)
    rena.set_round_manager(round_manager)
    # battle_map.build_adjacency_matrix()
    battle_map.place_circular_element((random.randint(0, 14), random.randint(0, 14)), Map.DIFFICULT_TERRAIN, random.randint(1, 2))
    battle_map.place_circular_element((random.randint(0, 14), random.randint(0, 14)), Map.DIFFICULT_TERRAIN, random.randint(1, 2))
    battle_map.place_circular_element((random.randint(0, 14), random.randint(0, 14)), Map.DIFFICULT_TERRAIN, random.randint(1, 2))
    battle_map.build_adjacency_matrix()
    # battle_map.get_path_to_enemy(rena, cyanwrath)
    round_manager.simulate_n(1)
    # round_manager.print_results()

