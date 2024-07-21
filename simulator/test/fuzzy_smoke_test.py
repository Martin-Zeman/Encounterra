import random
import time
import os

import pytest
import pickle

from simulator.battle_map import Map
from simulator.combatants.berserker import Berserker
from simulator.combatants.black_dragon_wyrmling import BlackDragonWyrmling
from simulator.combatants.brown_bear import BrownBear
from simulator.combatants.bugbear import Bugbear
from simulator.combatants.dire_wolf import DireWolf
from simulator.combatants.evil_mage import EvilMage
from simulator.combatants.giant_toad import GiantToad
from simulator.combatants.ogre import Ogre
from simulator.combatants.assassin_rogue_5lvl import AssassinRogue5Lvl
from simulator.combatants.quetzalcoatlus import Quetzalcoatlus
from simulator.combatants.stone_giant import StoneGiant
from simulator.logging.custom_logger import CustomLogger
from simulator.session import Session
from simulator.combatants.totem_barbarian_5lvl import TotemBarbarian5Lvl
from simulator.combatants.draconic_sorcerer_5lvl import DraconicSorcerer5Lvl
from simulator.combatants.goblin import Goblin
from simulator.combatants.dragonclaw_cultist import DragonclawCultist
from simulator.combatants.moon_druid_5lvl import MoonDruid5Lvl
from simulator.teams import Teams
import logging

from simulator.utils.utils import get_combatant_classes

logger = logging.getLogger("Encounterra")

SERIALIZE_DIR = 'serialized_objects'

@pytest.mark.slow
def test_random_matchup():
    CustomLogger(logging.INFO)
    for _ in range(100):
        Map.reset_singleton()
        combatant_pool = get_combatant_classes()
        combatant_black_list = [Quetzalcoatlus]
        combatant_pool = [c for c in combatant_pool if c not in combatant_black_list]
        session = Session()

        num_blue_combatants = random.randint(1, 4)
        num_red_combatants = random.randint(1, 4)

        blue_team = random.sample(combatant_pool, num_blue_combatants)
        red_team = random.sample(combatant_pool, num_red_combatants)
        red_team.append(BlackDragonWyrmling)
        logger.info(f"Starting a fuzzy test with:")
        logger.info(f"Blue team: {[str(c) for c in blue_team]}")
        logger.info(f"Red team: {[str(c) for c in red_team]}")

        for combatant in blue_team:
            session.add_combatant(combatant, Teams.Color.BLUE)
        for combatant in red_team:
            session.add_combatant(combatant, Teams.Color.RED)

        session.set_num_simulations(1)
        session.place_terrain_and_obstacles(Session.MapType.OBSTACLES_AND_DIFFICULT_TERRAIN.value)
        try:
            session.simulate(parallel=False)
        except Exception as e:
            timestamp = int(time.time())
            with open(os.path.join(SERIALIZE_DIR, f'battle_map_data_{timestamp}.pkl'), 'wb') as f:
                pickle.dump(Map.serialize_data(), f)
            with open(os.path.join(SERIALIZE_DIR, f'session_{timestamp}.pkl'), 'wb') as f:
                pickle.dump(session.serialize_data(), f)
            with open(os.path.join(SERIALIZE_DIR, f'exception_{timestamp}.txt'), 'w') as f:
                f.write(f"Fuzzy test with Blue team {blue_team} and Red team {red_team} raised an exception:\n{e}")

            assert False, f"Fuzzy test with Blue team {blue_team} and Red team {red_team} raised an exception {e}"