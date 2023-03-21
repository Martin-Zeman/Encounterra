import pytest
from simulator.combatants.totem_barbarian_5lvl import TotemBarbarian5Lvl
from simulator.effects.effect_tracker import EffectTracker
from simulator.combatants.bugbear import Bugbear
from simulator.combatants.faurung import Faurung
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
    return Map(15, teams)

@pytest.fixture()
def combatant1(effect_tracker):
    return Faurung(effect_tracker, "Faurung")

@pytest.fixture()
def combatant2(effect_tracker):
    return Goblin(effect_tracker, "Goblin")

@pytest.fixture()
def combatant3(effect_tracker):
    return Bugbear(effect_tracker, "Bugbear")

@pytest.fixture()
def combatant4(effect_tracker):
    return TotemBarbarian5Lvl(effect_tracker, "TotemBarbarian5Lvl")