import pytest

from simulator.combatants.giant_toad import GiantToad
from simulator.combatants.moon_druid_5lvl import MoonDruid5Lvl
from simulator.combatants.ogre import Ogre
from simulator.combatants.stone_giant import StoneGiant
from simulator.combatants.totem_barbarian_5lvl import TotemBarbarian5Lvl
from simulator.effects.effect_tracker import EffectTracker
from simulator.combatants.bugbear import Bugbear
from simulator.combatants.draconic_sorcerer_5lvl import DraconicSorcerer5Lvl
from simulator.combatants.goblin import Goblin
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
def test_draconic_sorcerer_5lvl(effect_tracker):
    return DraconicSorcerer5Lvl(effect_tracker, "DraconicSorcerer5lvl")

@pytest.fixture()
def test_goblin(effect_tracker):
    return Goblin(effect_tracker, "Goblin")

@pytest.fixture()
def test_bugbear(effect_tracker):
    return Bugbear(effect_tracker, "Bugbear")

@pytest.fixture()
def test_totem_barbarian(effect_tracker):
    return TotemBarbarian5Lvl(effect_tracker, "TotemBarbarian5Lvl")

@pytest.fixture()
def test_stone_giant(effect_tracker):
    return StoneGiant(effect_tracker, "StoneGiant")

@pytest.fixture()
def test_ogre(effect_tracker):
    return Ogre(effect_tracker, "Ogre")

@pytest.fixture()
def test_moon_druid(effect_tracker):
    return MoonDruid5Lvl(effect_tracker, "MoonDruid5Lvl")

@pytest.fixture()
def test_giant_toad(effect_tracker):
    return GiantToad(effect_tracker, "GiantToad")