from simulator.combatants.bugbear import Bugbear
from simulator.session import Session
from simulator.combatants.totem_barbarian_5lvl import TotemBarbarian5Lvl
from simulator.combatants.cyanwrath import Cyanwrath
from simulator.combatants.faurung import Faurung
from simulator.combatants.goblin import Goblin
from simulator.combatants.faurung_dt import FaurungDt
from simulator.combatants.dragonclaw_cultist import DragonclawCultist
from simulator.teams import Teams
import logging
import sys
import time
from simulator.logging.log_formatter import LogFormatter

if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    stdout_handler.setFormatter(LogFormatter())
    logger.addHandler(stdout_handler)
    session = Session()
    # session.add_combatant(Cyanwrath, Teams.Color.RED)
    session.add_combatant(Faurung, Teams.Color.BLUE)
    session.add_combatant(Bugbear, Teams.Color.RED)
    session.add_combatant(Bugbear, Teams.Color.RED)
    session.add_combatant(Bugbear, Teams.Color.RED)
    session.add_combatant(Bugbear, Teams.Color.RED)
    session.add_combatant(Goblin, Teams.Color.RED)
    # session.add_combatant(FaurungDt, Teams.Color.BLUE)
    # session.add_combatant(TotemBarbarian5Lvl, Teams.Color.BLUE)
    # session.add_combatant(DragonclawCultist, Teams.Color.RED)
    # session.add_combatant(DragonclawCultist, Teams.Color.RED)
    # session.add_combatant(DragonclawCultist, Teams.Color.RED)
    # session.add_combatant(DragonclawCultist, Teams.Color.RED)
    session.set_num_simulations(1)
    start_time = time.time()
    session.simulate(parallel=False)
    print("---Simulation took {:.1f} seconds ---".format((time.time() - start_time)))



