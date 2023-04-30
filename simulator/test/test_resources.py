import numpy as np
import pytest

from simulator.action_types import Action
from simulator.logging.custom_logger import CustomLogger, LogLevel
from simulator.resources import use_resources
from simulator.spells.fireball import FireballFactory
from simulator.spells.firebolt import FireboltFactory
from simulator.teams import Teams
from simulator.test.fixtures import combatant1, combatant2, combatant3, teams, effect_tracker, battle_map


def test_use_resources_spellslots(battle_map, teams, effect_tracker, combatant1, combatant2):
    CustomLogger(LogLevel.WARNING)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    firebolt_factory = FireboltFactory(1, Action.FIREBOLT, combatant1)
    firebolt = firebolt_factory.create(combatant2)
    fireball_factory = FireballFactory(1, Action.FIREBALL, combatant1)
    fireball = fireball_factory.create(np.array([0, 0]))

    assert combatant1.spellslots.get_spellslots(3) == 2
    assert combatant1.spellslots.get_spellslots(2) == 3
    assert combatant1.spellslots.get_spellslots(1) == 4
    use_resources(combatant1, firebolt, battle_map)
    assert combatant1.spellslots.get_spellslots(3) == 2
    assert combatant1.spellslots.get_spellslots(2) == 3
    assert combatant1.spellslots.get_spellslots(1) == 4
    use_resources(combatant1, fireball, battle_map)
    assert combatant1.spellslots.get_spellslots(3) == 1
    assert combatant1.spellslots.get_spellslots(2) == 3
    assert combatant1.spellslots.get_spellslots(1) == 4
    use_resources(combatant1, fireball, battle_map)
    assert combatant1.spellslots.get_spellslots(3) == 0
    assert combatant1.spellslots.get_spellslots(2) == 3
    assert combatant1.spellslots.get_spellslots(1) == 4
    combatant1.spellslots.reset()
    assert combatant1.spellslots.get_spellslots(3) == 2
    assert combatant1.spellslots.get_spellslots(2) == 3
    assert combatant1.spellslots.get_spellslots(1) == 4


def test_use_resources_already_cast_leveled_spell_this_turn(battle_map, teams, effect_tracker, combatant1, combatant2):
    CustomLogger(LogLevel.WARNING)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    firebolt_factory = FireboltFactory(1, Action.FIREBOLT, combatant1)
    firebolt = firebolt_factory.create(combatant2)
    fireball_factory = FireballFactory(1, Action.FIREBALL, combatant1)
    fireball = fireball_factory.create(np.array([0, 0]))

    assert not combatant1.already_cast_leveled_spell_this_turn
    use_resources(combatant1, firebolt, battle_map)
    assert not combatant1.already_cast_leveled_spell_this_turn
    use_resources(combatant1, fireball, battle_map)
    assert combatant1.already_cast_leveled_spell_this_turn


