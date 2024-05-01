import logging

from simulator.combatants.acolyte import Acolyte
from simulator.combatants.bandit_captain import BanditCaptain
from simulator.combatants.barbarian_1lvl import Barbarian1Lvl
from simulator.combatants.barbarian_2lvl import Barbarian2Lvl
from simulator.combatants.battlemaster_fighter_3lvl import BattlemasterFighter3Lvl
from simulator.combatants.battlemaster_fighter_4lvl import BattlemasterFighter4Lvl
from simulator.combatants.battlemaster_fighter_5lvl import BattlemasterFighter5Lvl
from simulator.combatants.berserker import Berserker
from simulator.combatants.black_dragon_wyrmling import BlackDragonWyrmling
from simulator.combatants.blue_dragon_wymling import BlueDragonWyrmling
from simulator.combatants.bugbear import Bugbear
from simulator.combatants.bugbear_chief import BugbearChief
from simulator.combatants.cultist_fanatic import CultistFanatic
from simulator.combatants.draconic_sorcerer_3lvl import DraconicSorcerer3Lvl
from simulator.combatants.draconic_sorcerer_4lvl import DraconicSorcerer4Lvl
from simulator.combatants.druid_1lvl import Druid1Lvl
from simulator.combatants.evil_mage import EvilMage
from simulator.combatants.fighter_2lvl import Fighter2Lvl
from simulator.combatants.fire_giant import FireGiant
from simulator.combatants.frost_giant import FrostGiant
from simulator.combatants.ghoul import Ghoul
from simulator.combatants.green_dragon_wyrmling import GreenDragonWyrmling
from simulator.combatants.hill_giant import HillGiant
from simulator.combatants.hobgoblin import Hobgoblin
from simulator.combatants.moon_druid_2lvl import MoonDruid2Lvl
from simulator.combatants.moon_druid_4lvl import MoonDruid4Lvl
from simulator.combatants.moon_druid_5lvl import MoonDruid5Lvl
from simulator.combatants.moon_druid_3lvl import MoonDruid3Lvl
from simulator.combatants.needle_blight import NeedleBlight
from simulator.combatants.night_hag import NightHag
from simulator.combatants.oath_of_vengeance_paladin_3lvl import OathOfVengeancePaladin3Lvl
from simulator.combatants.oath_of_vengeance_paladin_4lvl import OathOfVengeancePaladin4Lvl
from simulator.combatants.oath_of_vengeance_paladin_5lvl import OathOfVengeancePaladin5Lvl
from simulator.combatants.ogre import Ogre
from simulator.combatants.brown_bear import BrownBear
from simulator.combatants.owlbear import Owlbear
from simulator.combatants.paladin_1lvl import Paladin1Lvl
from simulator.combatants.paladin_2lvl import Paladin2Lvl
from simulator.combatants.rogue_1lvl import Rogue1Lvl
from simulator.combatants.rogue_2lvl import Rogue2Lvl
from simulator.combatants.skeleton import Skeleton
from simulator.combatants.stone_giant import StoneGiant
from simulator.combatants.totem_barbarian_4lvl import TotemBarbarian4Lvl
from simulator.combatants.twig_blight import TwigBlight
from simulator.combatants.white_dragon_wyrmling import WhiteDragonWyrmling
from simulator.combatants.young_black_dragon import YoungBlackDragon
from simulator.combatants.young_blue_dragon import YoungBlueDragon
from simulator.combatants.young_green_dragon import YoungGreenDragon
from simulator.combatants.young_red_dragon import YoungRedDragon
from simulator.combatants.young_white_dragon import YoungWhiteDragon
from simulator.combatants.zombie import Zombie
from simulator.logging.custom_logger import CustomLogger
from simulator.session import Session
from simulator.combatants.totem_barbarian_5lvl import TotemBarbarian5Lvl
from simulator.combatants.totem_barbarian_3lvl import TotemBarbarian3Lvl
from simulator.combatants.draconic_sorcerer_5lvl import DraconicSorcerer5Lvl
from simulator.combatants.goblin import Goblin
from simulator.combatants.dragonclaw_cultist import DragonclawCultist
from simulator.combatants.assassin_rogue_5lvl import AssassinRogue5Lvl
from simulator.combatants.assassin_rogue_3lvl import AssassinRogue3Lvl
from simulator.combatants.vampire_spawn import VampireSpawn
from simulator.combatants.stone_giant import StoneGiant
from simulator.combatants.assassin import Assassin
from simulator.combatants.saber_toothed_tiger import SaberToothedTiger
from simulator.combatants.giant_toad import GiantToad
from simulator.combatants.fighter_1lvl import Fighter1Lvl
from simulator.teams import Teams
import time

if __name__ == '__main__':
    CustomLogger(logging.INFO)
    session = Session()
    # session.add_combatant(MoonDruid5Lvl, Teams.Color.BLUE)
    session.add_combatant(MoonDruid4Lvl, Teams.Color.RED)
    # session.add_combatant(MoonDruid3Lvl, Teams.Color.BLUE)
    # session.add_combatant(MoonDruid2Lvl, Teams.Color.BLUE)
    # session.add_combatant(Acolyte, Teams.Color.BLUE)
    # session.add_combatant(DraconicSorcerer5Lvl, Teams.Color.BLUE)
    # session.add_combatant(DraconicSorcerer4Lvl, Teams.Color.RED)
    # session.add_combatant(DraconicSorcerer3Lvl, Teams.Color.RED)
    # session.add_combatant(AssassinRogue5Lvl, Teams.Color.BLUE)
    # session.add_combatant(AssassinRogue3Lvl, Teams.Color.BLUE)
    # session.add_combatant(GiantToad, Teams.Color.BLUE)
    # session.add_combatant(Assassin, Teams.Color.RED)
    # session.add_combatant(Ogre, Teams.Color.RED)
    # session.add_combatant(Ogre, Teams.Color.RED)
    # session.add_combatant(BanditCaptain, Teams.Color.RED)
    # session.add_combatant(Bugbear, Teams.Color.BLUE)
    # session.add_combatant(Bugbear, Teams.Color.BLUE)
    # session.add_combatant(Bugbear, Teams.Color.RED)
    # session.add_combatant(CultistFanatic, Teams.Color.BLUE)
    # session.add_combatant(Berserker, Teams.Color.BLUE)
    # session.add_combatant(BugbearChief, Teams.Color.RED)
    # session.add_combatant(TwigBlight, Teams.Color.RED)
    # session.add_combatant(TwigBlight, Teams.Color.RED)
    # session.add_combatant(TwigBlight, Teams.Color.RED)
    # session.add_combatant(NeedleBlight, Teams.Color.RED)
    # session.add_combatant(SaberToothedTiger, Teams.Color.RED)
    # session.add_combatant(SaberToothedTiger, Teams.Color.BLUE)
    # session.add_combatant(Goblin, Teams.Color.RED)
    # session.add_combatant(Goblin, Teams.Color.BLUE)
    # session.add_combatant(Barbarian2Lvl, Teams.Color.RED)
    # session.add_combatant(Barbarian1Lvl, Teams.Color.RED)
    # session.add_combatant(BrownBear, Teams.Color.BLUE)
    # session.add_combatant(Bugbear, Teams.Color.RED)
    # session.add_combatant(Bugbear, Teams.Color.BLUE)
    # session.add_combatant(TotemBarbarian5Lvl, Teams.Color.BLUE)
    session.add_combatant(TotemBarbarian4Lvl, Teams.Color.RED)
    # session.add_combatant(TotemBarbarian3Lvl, Teams.Color.RED)
    # session.add_combatant(StoneGiant, Teams.Color.BLUE)
    # session.add_combatant(VampireSpawn, Teams.Color.RED)
    # session.add_combatant(DragonclawCultist, Teams.Color.BLUE)
    # session.add_combatant(DragonclawCultist, Teams.Color.RED)
    # session.add_combatant(DragonclawCultist, Teams.Color.RED)
    # session.add_combatant(DragonclawCultist, Teams.Color.RED)
    # session.add_combatant(EvilMage, Teams.Color.BLUE)
    # session.add_combatant(NightHag, Teams.Color.BLUE)
    # session.add_combatant(Fighter1Lvl, Teams.Color.BLUE)
    # session.add_combatant(Rogue2Lvl, Teams.Color.BLUE)
    # session.add_combatant(Fighter2Lvl, Teams.Color.BLUE)
    # session.add_combatant(Skeleton, Teams.Color.RED)
    # session.add_combatant(Skeleton, Teams.Color.BLUE)
    # session.add_combatant(Paladin1Lvl, Teams.Color.BLUE)
    # session.add_combatant(Paladin2Lvl, Teams.Color.RED)
    # session.add_combatant(OathOfVengeancePaladin3Lvl, Teams.Color.BLUE)
    # session.add_combatant(BattlemasterFighter3Lvl, Teams.Color.RED)
    session.add_combatant(BattlemasterFighter4Lvl, Teams.Color.RED)
    # session.add_combatant(BattlemasterFighter5Lvl, Teams.Color.BLUE)
    # session.add_combatant(Rogue1Lvl, Teams.Color.RED)
    # session.add_combatant(Rogue2Lvl, Teams.Color.RED)
    # session.add_combatant(Fighter2Lvl, Teams.Color.RED)
    # session.add_combatant(Fighter2Lvl, Teams.Color.RED)
    # session.add_combatant(Druid1Lvl, Teams.Color.BLUE)
    # session.add_combatant(Druid1Lvl, Teams.Color.RED)
    # session.add_combatant(Zombie, Teams.Color.RED)
    # session.add_combatant(Zombie, Teams.Color.RED)
    # session.add_combatant(Hobgoblin, Teams.Color.RED)
    # session.add_combatant(Hobgoblin, Teams.Color.RED)
    # session.add_combatant(Hobgoblin, Teams.Color.RED)
    session.add_combatant(OathOfVengeancePaladin4Lvl, Teams.Color.RED)
    # session.add_combatant(OathOfVengeancePaladin5Lvl, Teams.Color.RED)
    # session.add_combatant(HillGiant, Teams.Color.BLUE)
    # session.add_combatant(FireGiant, Teams.Color.RED)
    # session.add_combatant(FrostGiant, Teams.Color.BLUE)
    # session.add_combatant(YoungGreenDragon, Teams.Color.BLUE)
    # session.add_combatant(YoungWhiteDragon, Teams.Color.BLUE)
    # session.add_combatant(YoungRedDragon, Teams.Color.RED)
    # session.add_combatant(YoungBlueDragon, Teams.Color.RED)
    # session.add_combatant(YoungBlackDragon, Teams.Color.RED)
    session.add_combatant(GreenDragonWyrmling, Teams.Color.BLUE)
    session.add_combatant(WhiteDragonWyrmling, Teams.Color.BLUE)
    session.add_combatant(BlackDragonWyrmling, Teams.Color.BLUE)
    session.add_combatant(BlueDragonWyrmling, Teams.Color.BLUE)
    # session.add_combatant(Owlbear, Teams.Color.RED)
    # session.add_combatant(Ghoul, Teams.Color.BLUE)
    # session.add_combatant(Ghoul, Teams.Color.RED)
    # session.add_combatant(Ghoul, Teams.Color.BLUE)
    # session.add_combatant(Ghoul, Teams.Color.RED)
    # session.add_combatant(Ghoul, Teams.Color.BLUE)
    session.set_num_simulations(1)
    start_time = time.time()
    session.place_terrain_and_obstacles(Session.MapType.OBSTACLES.value)
    session.simulate(parallel=False)
    print("---Simulation took {:.1f} seconds ---".format((time.time() - start_time)))



