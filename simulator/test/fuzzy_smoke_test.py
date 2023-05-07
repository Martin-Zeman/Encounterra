import random
import pytest
from simulator.combatants.bugbear import Bugbear
from simulator.combatants.ogre import Ogre
from simulator.combatants.stone_giant import StoneGiant
from simulator.logging.custom_logger import CustomLogger, LogLevel
from simulator.session import Session
from simulator.combatants.totem_barbarian_5lvl import TotemBarbarian5Lvl
from simulator.combatants.cyanwrath import Cyanwrath
from simulator.combatants.faurung import Faurung
from simulator.combatants.goblin import Goblin
from simulator.combatants.dragonclaw_cultist import DragonclawCultist
from simulator.teams import Teams

@pytest.mark.skip( reason='Manual test only')
@pytest.mark.parametrize('execution_number', range(1))
def test_random_matchup(execution_number):
    CustomLogger(LogLevel.INFO)
    combatant_pool = [Faurung, StoneGiant, Ogre, Bugbear, Goblin, TotemBarbarian5Lvl]
    session = Session()

    num_blue_combatants = random.randint(1, 4)
    num_red_combatants = random.randint(1, 4)

    blue_team = random.sample(combatant_pool, num_blue_combatants)
    red_team = random.sample(combatant_pool, num_red_combatants)

    for combatant in blue_team:
        session.add_combatant(combatant, Teams.Color.BLUE)
    for combatant in red_team:
        session.add_combatant(combatant, Teams.Color.RED)

    session.set_num_simulations(1)
    try:
        session.simulate(parallel=False)
    except Exception as e:
        assert False, f"Fuzzy test with Blue team {blue_team} and Red team {red_team} raised an exception {e}"