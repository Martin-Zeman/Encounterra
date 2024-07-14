import pytest

from simulator.combatants.assassin_rogue_5lvl import AssassinRogue5Lvl
from simulator.combatants.assassin_rogue_3lvl import AssassinRogue3Lvl
from simulator.combatants.battlemaster_fighter_3lvl import BattlemasterFighter3Lvl
from simulator.combatants.battlemaster_fighter_5lvl import BattlemasterFighter5Lvl
from simulator.combatants.dire_wolf import DireWolf
from simulator.combatants.dragonclaw_cultist import DragonclawCultist
from simulator.combatants.druid_1lvl import Druid1Lvl
from simulator.combatants.fighter_1lvl import Fighter1Lvl
from simulator.combatants.fighter_2lvl import Fighter2Lvl
from simulator.combatants.ghoul import Ghoul
from simulator.combatants.giant_toad import GiantToad
from simulator.combatants.giant_constrictor_snake import GiantConstrictorSnake
from simulator.combatants.green_dragon_wyrmling import GreenDragonWyrmling
from simulator.combatants.hobgoblin import Hobgoblin
from simulator.combatants.moon_druid_5lvl import MoonDruid5Lvl
from simulator.combatants.night_hag import NightHag
from simulator.combatants.ogre import Ogre
from simulator.combatants.bandit_captain import BanditCaptain
from simulator.combatants.orc import Orc
from simulator.combatants.paladin_1lvl import Paladin1Lvl
from simulator.combatants.skeleton import Skeleton
from simulator.combatants.twig_blight import TwigBlight
from simulator.combatants.stone_giant import StoneGiant
from simulator.combatants.totem_barbarian_5lvl import TotemBarbarian5Lvl
from simulator.combatants.vampire_spawn import VampireSpawn
from simulator.combatants.young_green_dragon import YoungGreenDragon
from simulator.effects.effect_tracker import EffectTracker
from simulator.combatants.bugbear import Bugbear
from simulator.combatants.draconic_sorcerer_5lvl import DraconicSorcerer5Lvl
from simulator.combatants.draconic_sorcerer_3lvl import DraconicSorcerer3Lvl
from simulator.combatants.goblin import Goblin
from simulator.combatants.brown_bear import BrownBear
from simulator.combatants.saber_toothed_tiger import SaberToothedTiger
from simulator.combatants.berserker import Berserker
from simulator.combatants.evil_mage import EvilMage
from simulator.combatants.commoner import Commoner
from simulator.teams import Teams
from simulator.battle_map import Map


@pytest.fixture()
def teams():
    return Teams()


@pytest.fixture()
def effect_tracker():
    return EffectTracker()


@pytest.fixture()
def battle_map(teams):
    Map.reset_singleton()
    ret = Map(15, teams)
    ret.clear_caches()
    return ret


@pytest.fixture()
def test_draconic_sorcerer_5lvl():
    return DraconicSorcerer5Lvl()


@pytest.fixture()
def test_draconic_sorcerer_3lvl():
    return DraconicSorcerer3Lvl()


@pytest.fixture()
def test_goblin():
    return Goblin()


@pytest.fixture()
def test_bugbear():
    return Bugbear()


@pytest.fixture()
def test_evil_mage():
    return EvilMage()


@pytest.fixture()
def test_totem_barbarian():
    return TotemBarbarian5Lvl()


@pytest.fixture()
def test_night_hag():
    return NightHag()


@pytest.fixture()
def test_commoner():
    return Commoner()


@pytest.fixture()
def test_stone_giant():
    return StoneGiant()


@pytest.fixture()
def test_ogre():
    return Ogre()


@pytest.fixture()
def test_moon_druid():
    return MoonDruid5Lvl()


@pytest.fixture()
def test_druid_lvl_1():
    return Druid1Lvl()


@pytest.fixture()
def test_paladin_lvl_1():
    return Paladin1Lvl()


@pytest.fixture()
def test_fighter_lvl_1():
    return Fighter1Lvl()


@pytest.fixture()
def test_fighter_lvl_2():
    return Fighter2Lvl()


@pytest.fixture()
def test_battle_master_fighter_lvl_3():
    return BattlemasterFighter3Lvl()


@pytest.fixture()
def test_battle_master_fighter_lvl_5():
    return BattlemasterFighter5Lvl()


@pytest.fixture()
def test_vampire_spawn():
    return VampireSpawn()


@pytest.fixture()
def test_giant_toad():
    return GiantToad("GiantToad")


@pytest.fixture()
def test_giant_constrictor_snake():
    return GiantConstrictorSnake()


@pytest.fixture()
def test_twig_blight():
    return TwigBlight()


@pytest.fixture()
def test_bandit_captain():
    return BanditCaptain()


@pytest.fixture()
def test_sabertoother_tiger():
    return SaberToothedTiger()


@pytest.fixture()
def test_dragonclaw_cultist():
    return DragonclawCultist()


@pytest.fixture()
def test_brown_bear():
    return BrownBear("BrownBear")


@pytest.fixture()
def test_dire_wolf():
    return DireWolf()


@pytest.fixture()
def test_berserker():
    return Berserker()


@pytest.fixture()
def test_assassin_rogue():
    return AssassinRogue5Lvl()


@pytest.fixture()
def test_assassin_rogue_3lvl():
    return AssassinRogue3Lvl()


@pytest.fixture()
def test_young_green_dragon():
    return YoungGreenDragon()


@pytest.fixture()
def test_green_dragon_wyrmling():
    return GreenDragonWyrmling()


@pytest.fixture()
def test_skeleton():
    return Skeleton()


@pytest.fixture()
def test_hobgoblin():
    return Hobgoblin()


@pytest.fixture()
def test_ghoul():
    return Ghoul()

@pytest.fixture()
def test_orc():
    return Orc()
