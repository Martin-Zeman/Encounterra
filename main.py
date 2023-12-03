import logging

from simulator.combatants.bandit_captain import BanditCaptain
from simulator.combatants.berserker import Berserker
from simulator.combatants.bugbear import Bugbear
from simulator.combatants.bugbear_chief import BugbearChief
from simulator.combatants.cultist_fanatic import CultistFanatic
from simulator.combatants.evil_mage import EvilMage
from simulator.combatants.moon_druid_5lvl import MoonDruid5Lvl
from simulator.combatants.needle_blight import NeedleBlight
from simulator.combatants.ogre import Ogre
from simulator.combatants.brown_bear import BrownBear
from simulator.combatants.stone_giant import StoneGiant
from simulator.combatants.twig_blight import TwigBlight
from simulator.logging.custom_logger import CustomLogger
from simulator.session import Session
from simulator.combatants.totem_barbarian_5lvl import TotemBarbarian5Lvl
from simulator.combatants.draconic_sorcerer_5lvl import DraconicSorcerer5Lvl
from simulator.combatants.goblin import Goblin
from simulator.combatants.dragonclaw_cultist import DragonclawCultist
from simulator.combatants.assassin_rogue_5lvl import AssassinRogue5Lvl
from simulator.combatants.vampire_spawn import VampireSpawn
from simulator.combatants.stone_giant import StoneGiant
from simulator.combatants.assassin import Assassin
from simulator.teams import Teams
import time

if __name__ == '__main__':
    CustomLogger(logging.INFO)
    session = Session()
    # session.add_combatant(MoonDruid5Lvl, Teams.Color.BLUE)
    # session.add_combatant(DraconicSorcerer5Lvl, Teams.Color.BLUE)
    # session.add_combatant(AssassinRogue5Lvl, Teams.Color.RED)
    # session.add_combatant(Assassin, Teams.Color.RED)
    # session.add_combatant(Ogre, Teams.Color.RED)
    # session.add_combatant(BanditCaptain, Teams.Color.RED)
    session.add_combatant(Bugbear, Teams.Color.RED)
    session.add_combatant(Bugbear, Teams.Color.RED)
    session.add_combatant(Bugbear, Teams.Color.RED)
    session.add_combatant(CultistFanatic, Teams.Color.BLUE)
    session.add_combatant(Berserker, Teams.Color.BLUE)
    # session.add_combatant(BugbearChief, Teams.Color.RED)
    # session.add_combatant(TwigBlight, Teams.Color.RED)
    # session.add_combatant(TwigBlight, Teams.Color.RED)
    # session.add_combatant(TwigBlight, Teams.Color.RED)
    # session.add_combatant(NeedleBlight, Teams.Color.RED)
    # session.add_combatant(Goblin, Teams.Color.BLUE)
    # session.add_combatant(BrownBear, Teams.Color.BLUE)
    # session.add_combatant(Bugbear, Teams.Color.BLUE)
    # session.add_combatant(Bugbear, Teams.Color.RED)
    # session.add_combatant(FaurungDt, Teams.Color.BLUE)
    # session.add_combatant(TotemBarbarian5Lvl, Teams.Color.BLUE)
    # session.add_combatant(StoneGiant, Teams.Color.BLUE)
    # session.add_combatant(VampireSpawn, Teams.Color.RED)
    session.add_combatant(DragonclawCultist, Teams.Color.BLUE)
    # session.add_combatant(DragonclawCultist, Teams.Color.RED)
    # session.add_combatant(DragonclawCultist, Teams.Color.RED)
    # session.add_combatant(DragonclawCultist, Teams.Color.RED)
    # session.add_combatant(EvilMage, Teams.Color.BLUE)
    session.set_num_simulations(1)
    start_time = time.time()
    session.simulate(parallel=False)
    print("---Simulation took {:.1f} seconds ---".format((time.time() - start_time)))



