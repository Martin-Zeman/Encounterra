import random
import pytest

from simulator.battle_map import Map
from simulator.combatants.brown_bear import BrownBear
from simulator.combatants.bugbear import Bugbear
from simulator.combatants.dire_wolf import DireWolf
from simulator.combatants.evil_mage import EvilMage
from simulator.combatants.giant_toad import GiantToad
from simulator.combatants.ogre import Ogre
from simulator.combatants.stone_giant import StoneGiant
from simulator.logging.custom_logger import CustomLogger, LogLevel
from simulator.session import Session
from simulator.combatants.totem_barbarian_5lvl import TotemBarbarian5Lvl
from simulator.combatants.cyanwrath import Cyanwrath
from simulator.combatants.draconic_sorcerer_5lvl import DraconicSorcerer5Lvl
from simulator.combatants.goblin import Goblin
from simulator.combatants.dragonclaw_cultist import DragonclawCultist
from simulator.combatants.moon_druid_5lvl import MoonDruid5Lvl
from simulator.teams import Teams
import logging

logger = logging.getLogger("EncounTroll")

@pytest.mark.slow
def test_random_matchup():
    CustomLogger(LogLevel.INFO)
    for _ in range(100):
        Map.reset_singleton()
        combatant_pool = [DraconicSorcerer5Lvl, StoneGiant, Ogre, Bugbear, Goblin, TotemBarbarian5Lvl, DragonclawCultist, MoonDruid5Lvl, GiantToad, DireWolf, BrownBear,
                          EvilMage]
        session = Session()

        num_blue_combatants = random.randint(1, 4)
        num_red_combatants = random.randint(1, 4)
        # num_red_combatants = random.randint(1, 2)

        blue_team = random.sample(combatant_pool, num_blue_combatants)
        # blue_team = [GiantToad]
        red_team = random.sample(combatant_pool, num_red_combatants)
        # red_team = random.sample(combatant_pool, num_red_combatants)
        logger.info(f"Starting a fuzzy test with:")
        logger.info(f"Blue team: {blue_team}")
        logger.info(f"Red team: {red_team}")

        for combatant in blue_team:
            session.add_combatant(combatant, Teams.Color.BLUE)
        for combatant in red_team:
            session.add_combatant(combatant, Teams.Color.RED)

        session.set_num_simulations(1)
        try:
            session.simulate(parallel=False)
        except Exception as e:
            assert False, f"Fuzzy test with Blue team {blue_team} and Red team {red_team} raised an exception {e}"