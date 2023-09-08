import random
import pytest

from ..battle_map import Map
from ..combatants.brown_bear import BrownBear
from ..combatants.bugbear import Bugbear
from ..combatants.dire_wolf import DireWolf
from ..combatants.evil_mage import EvilMage
from ..combatants.giant_toad import GiantToad
from ..combatants.ogre import Ogre
from ..combatants.assassin_rogue_5lvl import AssassinRogue5Lvl
from ..combatants.stone_giant import StoneGiant
from ..logging.custom_logger import CustomLogger
from ..session import Session
from ..combatants.totem_barbarian_5lvl import TotemBarbarian5Lvl
from ..combatants.draconic_sorcerer_5lvl import DraconicSorcerer5Lvl
from ..combatants.goblin import Goblin
from ..combatants.dragonclaw_cultist import DragonclawCultist
from ..combatants.moon_druid_5lvl import MoonDruid5Lvl
from ..teams import Teams
import logging

logger = logging.getLogger("Encounterra")

@pytest.mark.slow
def test_random_matchup():
    CustomLogger(logging.INFO)
    for _ in range(100):
        Map.reset_singleton()
        combatant_pool = [DraconicSorcerer5Lvl, StoneGiant, Ogre, Bugbear, Goblin, TotemBarbarian5Lvl, DragonclawCultist, MoonDruid5Lvl, GiantToad, DireWolf, BrownBear,
                          EvilMage, AssassinRogue5Lvl]
        session = Session()

        num_blue_combatants = random.randint(1, 4)
        num_red_combatants = random.randint(1, 4)
        # num_red_combatants = random.randint(1, 2)

        blue_team = random.sample(combatant_pool, num_blue_combatants)
        # blue_team = [GiantToad]
        red_team = random.sample(combatant_pool, num_red_combatants)
        # red_team.append(AssassinRogue5Lvl)
        # red_team = random.sample(combatant_pool, num_red_combatants)
        logger.info(f"Starting a fuzzy test with:")
        logger.info(f"Blue team: {[str(c) for c in blue_team]}")
        logger.info(f"Red team: {[str(c) for c in red_team]}")

        for combatant in blue_team:
            session.add_combatant(combatant, Teams.Color.BLUE)
        for combatant in red_team:
            session.add_combatant(combatant, Teams.Color.RED)

        session.set_num_simulations(1)
        try:
            session.simulate(parallel=False)
        except Exception as e:
            assert False, f"Fuzzy test with Blue team {blue_team} and Red team {red_team} raised an exception {e}"