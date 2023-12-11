import pytest

from ..combatants.assassin_rogue_5lvl import AssassinRogue5Lvl
from ..combatants.dire_wolf import DireWolf
from ..combatants.dragonclaw_cultist import DragonclawCultist
from ..combatants.giant_toad import GiantToad
from ..combatants.giant_constrictor_snake import GiantConstrictorSnake
from ..combatants.moon_druid_5lvl import MoonDruid5Lvl
from ..combatants.ogre import Ogre
from ..combatants.bandit_captain import BanditCaptain
from ..combatants.twig_blight import TwigBlight
from ..combatants.stone_giant import StoneGiant
from ..combatants.totem_barbarian_5lvl import TotemBarbarian5Lvl
from ..effects.effect_tracker import EffectTracker
from ..combatants.bugbear import Bugbear
from ..combatants.draconic_sorcerer_5lvl import DraconicSorcerer5Lvl
from ..combatants.draconic_sorcerer_3lvl import DraconicSorcerer3Lvl
from ..combatants.goblin import Goblin
from ..combatants.brown_bear import BrownBear
from ..combatants.saber_toothed_tiger import SaberToothedTiger
from ..combatants.berserker import Berserker
from ..combatants.evil_mage import EvilMage
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
def test_stone_giant():
    return StoneGiant()


@pytest.fixture()
def test_ogre():
    return Ogre()


@pytest.fixture()
def test_moon_druid():
    return MoonDruid5Lvl()


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
