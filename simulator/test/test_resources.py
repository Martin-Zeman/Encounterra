import logging

import numpy as np

from ..actions.action_types import Action
from ..logging.custom_logger import CustomLogger
from ..resources import use_resources
from ..spells.fireball import FireballFactory
from ..spells.firebolt import FireboltFactory
from ..teams import Teams
from ..test.fixtures import test_draconic_sorcerer_5lvl, test_goblin, teams, effect_tracker, battle_map

def test_use_resources_spellslots(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_goblin):
    CustomLogger(logging.WARNING)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    firebolt_factory = FireboltFactory(1, Action.FIREBOLT, test_draconic_sorcerer_5lvl)
    firebolt = firebolt_factory.create(test_goblin)
    fireball_factory = FireballFactory(1, Action.FIREBALL, test_draconic_sorcerer_5lvl)
    fireball = fireball_factory.create(np.array([0, 0]))

    assert test_draconic_sorcerer_5lvl.spellslots.get_spellslots(3) == 2
    assert test_draconic_sorcerer_5lvl.spellslots.get_spellslots(2) == 3
    assert test_draconic_sorcerer_5lvl.spellslots.get_spellslots(1) == 4
    use_resources(test_draconic_sorcerer_5lvl, firebolt)
    assert test_draconic_sorcerer_5lvl.spellslots.get_spellslots(3) == 2
    assert test_draconic_sorcerer_5lvl.spellslots.get_spellslots(2) == 3
    assert test_draconic_sorcerer_5lvl.spellslots.get_spellslots(1) == 4
    use_resources(test_draconic_sorcerer_5lvl, fireball)
    assert test_draconic_sorcerer_5lvl.spellslots.get_spellslots(3) == 1
    assert test_draconic_sorcerer_5lvl.spellslots.get_spellslots(2) == 3
    assert test_draconic_sorcerer_5lvl.spellslots.get_spellslots(1) == 4
    use_resources(test_draconic_sorcerer_5lvl, fireball)
    assert test_draconic_sorcerer_5lvl.spellslots.get_spellslots(3) == 0
    assert test_draconic_sorcerer_5lvl.spellslots.get_spellslots(2) == 3
    assert test_draconic_sorcerer_5lvl.spellslots.get_spellslots(1) == 4
    test_draconic_sorcerer_5lvl.spellslots.reset()
    assert test_draconic_sorcerer_5lvl.spellslots.get_spellslots(3) == 2
    assert test_draconic_sorcerer_5lvl.spellslots.get_spellslots(2) == 3
    assert test_draconic_sorcerer_5lvl.spellslots.get_spellslots(1) == 4


def test_use_resources_already_cast_leveled_spell_this_turn(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_goblin):
    CustomLogger(logging.WARNING)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    firebolt_factory = FireboltFactory(1, Action.FIREBOLT, test_draconic_sorcerer_5lvl)
    firebolt = firebolt_factory.create(test_goblin)
    fireball_factory = FireballFactory(1, Action.FIREBALL, test_draconic_sorcerer_5lvl)
    fireball = fireball_factory.create(np.array([0, 0]))

    assert not test_draconic_sorcerer_5lvl.already_cast_leveled_spell_this_turn
    use_resources(test_draconic_sorcerer_5lvl, firebolt)
    assert not test_draconic_sorcerer_5lvl.already_cast_leveled_spell_this_turn
    use_resources(test_draconic_sorcerer_5lvl, fireball)
    assert test_draconic_sorcerer_5lvl.already_cast_leveled_spell_this_turn


