import pytest

from simulator.combatants.dragonclaw_cultist import DragonclawCultist
from simulator.combatants.giant_toad import GiantToad
from simulator.combatants.moon_druid_5lvl import MoonDruid5Lvl
from simulator.combatants.ogre import Ogre
from simulator.combatants.stone_giant import StoneGiant
from simulator.combatants.totem_barbarian_5lvl import TotemBarbarian5Lvl
from simulator.effects.effect_tracker import EffectTracker
from simulator.combatants.bugbear import Bugbear
from simulator.combatants.draconic_sorcerer_5lvl import DraconicSorcerer5Lvl
from simulator.combatants.goblin import Goblin
from simulator.combatants.brown_bear import BrownBear
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
    return Map(15, teams)

@pytest.fixture()
def test_draconic_sorcerer_5lvl():
    return DraconicSorcerer5Lvl("DraconicSorcerer5lvl")

@pytest.fixture()
def test_goblin():
    return Goblin("Goblin")

@pytest.fixture()
def test_bugbear():
    return Bugbear("Bugbear")

@pytest.fixture()
def test_totem_barbarian():
    return TotemBarbarian5Lvl("TotemBarbarian5Lvl")

@pytest.fixture()
def test_stone_giant():
    return StoneGiant("StoneGiant")

@pytest.fixture()
def test_ogre():
    return Ogre("Ogre")

@pytest.fixture()
def test_moon_druid():
    return MoonDruid5Lvl("MoonDruid5Lvl")

@pytest.fixture()
def test_giant_toad():
    return GiantToad("GiantToad")

@pytest.fixture()
def test_dragonclaw_cultist():
    return DragonclawCultist("DragonclawCultist")

@pytest.fixture()
def test_brown_bear():
    return BrownBear("BrownBear")
