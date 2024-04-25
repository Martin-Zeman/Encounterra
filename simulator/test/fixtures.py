import pytest

from ..combatants.assassin_rogue_5lvl import AssassinRogue5Lvl
from ..combatants.battlemaster_fighter_3lvl import BattlemasterFighter3Lvl
from ..combatants.dire_wolf import DireWolf
from ..combatants.dragonclaw_cultist import DragonclawCultist
from ..combatants.druid_1lvl import Druid1Lvl
from ..combatants.fighter_1lvl import Fighter1Lvl
from ..combatants.fighter_2lvl import Fighter2Lvl
from ..combatants.giant_toad import GiantToad
from ..combatants.giant_constrictor_snake import GiantConstrictorSnake
from ..combatants.green_dragon_wyrmling import GreenDragonWyrmling
from ..combatants.hobgoblin import Hobgoblin
from ..combatants.moon_druid_5lvl import MoonDruid5Lvl
from ..combatants.night_hag import NightHag
from ..combatants.ogre import Ogre
from ..combatants.bandit_captain import BanditCaptain
from ..combatants.paladin_1lvl import Paladin1Lvl
from ..combatants.skeleton import Skeleton
from ..combatants.twig_blight import TwigBlight
from ..combatants.stone_giant import StoneGiant
from ..combatants.totem_barbarian_5lvl import TotemBarbarian5Lvl
from ..combatants.vampire_spawn import VampireSpawn
from ..combatants.young_green_dragon import YoungGreenDragon
from ..effects.effect_tracker import EffectTracker
from ..combatants.bugbear import Bugbear
from ..combatants.draconic_sorcerer_5lvl import DraconicSorcerer5Lvl
from ..combatants.draconic_sorcerer_3lvl import DraconicSorcerer3Lvl
from ..combatants.goblin import Goblin
from ..combatants.brown_bear import BrownBear
from ..combatants.saber_toothed_tiger import SaberToothedTiger
from ..combatants.berserker import Berserker
from ..combatants.evil_mage import EvilMage
from ..combatants.commoner import Commoner
from ..teams import Teams
from ..battle_map import Map

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
