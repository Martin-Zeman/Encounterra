import logging

import numpy as np

from ..actions.action_types import Action
from ..logging.custom_logger import CustomLogger
from ..resources import use_resources, ResourceDepletionLevel
from ..spells.fireball import FireballFactory
from ..spells.firebolt import FireboltFactory
from ..teams import Teams
from ..test.fixtures import test_draconic_sorcerer_5lvl, test_goblin, test_totem_barbarian, teams, effect_tracker, battle_map

def test_use_resources_spellslots(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_goblin):
    CustomLogger(logging.WARNING)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    firebolt_factory = FireboltFactory(1, Action.FIREBOLT, test_draconic_sorcerer_5lvl, test_draconic_sorcerer_5lvl.spellslots)
    firebolt = firebolt_factory.create(test_goblin)
    fireball_factory = FireballFactory(1, Action.FIREBALL, test_draconic_sorcerer_5lvl, test_draconic_sorcerer_5lvl.spellslots)
    fireball = fireball_factory.create(np.array([0, 0]))

    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=3) == 2
    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=2) == 3
    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=1) == 4
    use_resources(test_draconic_sorcerer_5lvl, firebolt)
    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=3) == 2
    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=2) == 3
    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=1) == 4
    use_resources(test_draconic_sorcerer_5lvl, fireball)
    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=3) == 1
    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=2) == 3
    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=1) == 4
    use_resources(test_draconic_sorcerer_5lvl, fireball)
    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=3) == 0
    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=2) == 3
    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=1) == 4
    test_draconic_sorcerer_5lvl.spellslots.reset()
    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=3) == 2
    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=2) == 3
    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=1) == 4


def test_use_resources_already_cast_leveled_spell_this_turn(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_goblin):
    CustomLogger(logging.WARNING)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    firebolt_factory = FireboltFactory(1, Action.FIREBOLT, test_draconic_sorcerer_5lvl, test_draconic_sorcerer_5lvl.spellslots)
    firebolt = firebolt_factory.create(test_goblin)
    fireball_factory = FireballFactory(1, Action.FIREBALL, test_draconic_sorcerer_5lvl, test_draconic_sorcerer_5lvl.spellslots)
    fireball = fireball_factory.create(np.array([0, 0]))

    assert not test_draconic_sorcerer_5lvl.already_cast_leveled_spell_this_turn
    use_resources(test_draconic_sorcerer_5lvl, firebolt)
    assert not test_draconic_sorcerer_5lvl.already_cast_leveled_spell_this_turn
    use_resources(test_draconic_sorcerer_5lvl, fireball)
    assert test_draconic_sorcerer_5lvl.already_cast_leveled_spell_this_turn


def test_deplete_resource_spellslots(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl):
    CustomLogger(logging.WARNING)
    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=3) == 2
    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=2) == 3
    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=1) == 4
    test_draconic_sorcerer_5lvl.spellslots.deplete_resource(ResourceDepletionLevel.PARTIALLY_DEPLETED)
    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=3) == 1
    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=2) == 1
    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=1) == 2
    test_draconic_sorcerer_5lvl.spellslots.deplete_resource(ResourceDepletionLevel.FULLY_DEPLETED)
    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=3) == 0
    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=2) == 0
    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=1) == 0
    # Resource depletion is a setter, i.e. it can even restore resources
    test_draconic_sorcerer_5lvl.spellslots.deplete_resource(ResourceDepletionLevel.PARTIALLY_DEPLETED)
    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=3) == 1
    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=2) == 1
    assert test_draconic_sorcerer_5lvl.spellslots.get_resource(level=1) == 2


def test_deplete_resource_uses(battle_map, teams, effect_tracker, test_totem_barbarian):
    CustomLogger(logging.WARNING)
    assert test_totem_barbarian.resources[0].has_resource()
    assert test_totem_barbarian.resources[0].get_resource() == 3
    test_totem_barbarian.resources[0].use_resource()
    assert test_totem_barbarian.resources[0].get_resource() == 2
    test_totem_barbarian.resources[0].use_resource()
    assert test_totem_barbarian.resources[0].get_resource() == 1
    test_totem_barbarian.resources[0].use_resource()
    assert test_totem_barbarian.resources[0].get_resource() == 0
    assert not test_totem_barbarian.resources[0].has_resource()
    test_totem_barbarian.resources[0].deplete_resource(ResourceDepletionLevel.PARTIALLY_DEPLETED)
    assert test_totem_barbarian.resources[0].get_resource() == 1
    test_totem_barbarian.resources[0].deplete_resource(ResourceDepletionLevel.FULLY_DEPLETED)
    assert test_totem_barbarian.resources[0].get_resource() == 0
    assert not test_totem_barbarian.resources[0].has_resource()


def test_deplete_resources_uses_on_combatant(battle_map, teams, effect_tracker, test_totem_barbarian):
    CustomLogger(logging.WARNING)
    assert test_totem_barbarian.resources[0].has_resource()
    assert test_totem_barbarian.resources[0].get_resource() == 3
    test_totem_barbarian.deplete_resources(ResourceDepletionLevel.PARTIALLY_DEPLETED)
    assert test_totem_barbarian.resources[0].get_resource() == 1
    test_totem_barbarian.deplete_resources(ResourceDepletionLevel.FULLY_DEPLETED)
    assert test_totem_barbarian.resources[0].get_resource() == 0
    assert not test_totem_barbarian.resources[0].has_resource()


def test_deplete_resources_on_combatant_with_no_resources(battle_map, teams, effect_tracker, test_goblin):
    assert not test_goblin.resources
    try:
        test_goblin.deplete_resources(ResourceDepletionLevel.PARTIALLY_DEPLETED)
        test_goblin.deplete_resources(ResourceDepletionLevel.FULLY_DEPLETED)
    except Exception as e:
        assert False, f"Raised an exception {e}"
