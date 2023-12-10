import pytest

from ..combatants.assassin_rogue_5lvl import AssassinRogue5Lvl
from ..combatants.dire_wolf import DireWolf
from ..combatants.dragonclaw_cultist import DragonclawCultist
from ..combatants.giant_toad import GiantToad
from ..combatants.moon_druid_5lvl import MoonDruid5Lvl
from ..combatants.ogre import Ogre
from ..combatants.stone_giant import StoneGiant
from ..combatants.totem_barbarian_5lvl import TotemBarbarian5Lvl
from ..effects.effect_tracker import EffectTracker
from ..combatants.bugbear import Bugbear
from ..combatants.draconic_sorcerer_5lvl import DraconicSorcerer5Lvl
from ..combatants.draconic_sorcerer_3lvl import DraconicSorcerer3Lvl
from ..combatants.goblin import Goblin
from ..combatants.brown_bear import BrownBear
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
def test_dragonclaw_cultist():
    return DragonclawCultist()

@pytest.fixture()
def test_brown_bear():
    return BrownBear("BrownBear")

@pytest.fixture()
def test_dire_wolf():
    return DireWolf()

@pytest.fixture()
def test_assassin_rogue():
    return AssassinRogue5Lvl()
