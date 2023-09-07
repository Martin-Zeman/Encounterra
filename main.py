from simulator.combatants.bugbear import Bugbear
from simulator.combatants.moon_druid_5lvl import MoonDruid5Lvl
from simulator.combatants.ogre import Ogre
from simulator.combatants.stone_giant import StoneGiant
from simulator.logging.custom_logger import CustomLogger, LogLevel
from simulator.session import Session
from simulator.combatants.totem_barbarian_5lvl import TotemBarbarian5Lvl
from simulator.combatants.draconic_sorcerer_5lvl import DraconicSorcerer5Lvl
from simulator.combatants.goblin import Goblin
from simulator.combatants.dragonclaw_cultist import DragonclawCultist
from simulator.teams import Teams
import time

if __name__ == '__main__':
    CustomLogger(LogLevel.INFO)
    session = Session()
    # session.add_combatant(MoonDruid5Lvl, Teams.Color.BLUE)
    # session.add_combatant(MoonDruid5Lvl, Teams.Color.RED)
    # session.add_combatant(Ogre, Teams.Color.RED)
    session.add_combatant(Bugbear, Teams.Color.RED)
    # session.add_combatant(Bugbear, Teams.Color.RED)
    # session.add_combatant(Goblin, Teams.Color.RED)
    # session.add_combatant(Bugbear, Teams.Color.BLUE)
    # session.add_combatant(Bugbear, Teams.Color.RED)
    # session.add_combatant(FaurungDt, Teams.Color.BLUE)
    # session.add_combatant(TotemBarbarian5Lvl, Teams.Color.BLUE)
    session.add_combatant(DragonclawCultist, Teams.Color.BLUE)
    # session.add_combatant(DragonclawCultist, Teams.Color.RED)
    # session.add_combatant(DragonclawCultist, Teams.Color.RED)
    # session.add_combatant(DragonclawCultist, Teams.Color.RED)
    session.set_num_simulations(1)
    start_time = time.time()
    session.simulate(parallel=False)
    print("---Simulation took {:.1f} seconds ---".format((time.time() - start_time)))



