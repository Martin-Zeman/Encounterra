import logging

import numpy as np

from ..action_resolver import ActionResolver
from ..actions.action_selector import get_action
from ..actions.action_types import Action
from ..logging.custom_logger import CustomLogger
from ..spells.haste import HasteFactory
from ..teams import Teams
from ..test.fixtures import test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, test_totem_barbarian, test_stone_giant, test_ogre, teams, effect_tracker, battle_map

def test_haste(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_bugbear, test_totem_barbarian):
    """
    We assert that a hasted bugbear utilizes both its regular attack and hasted attack independently, although each attack must be used
    once.
    """
    CustomLogger(logging.WARNING)

    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 0]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 4]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([5, 4]))  # Have to set it for fireball placement
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_draconic_sorcerer_5lvl, test_bugbear, test_totem_barbarian]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)

    try:
        hf = HasteFactory(Action.HASTE, test_draconic_sorcerer_5lvl)
        haste = hf.create(test_bugbear)
        action_resolver.resolve_action(haste, test_draconic_sorcerer_5lvl)

        actoid1 = get_action(test_bugbear)
        action_resolver.resolve_action(actoid1, test_bugbear)
        actoid2 = get_action(test_bugbear)
        assert str(actoid1) == "Morningstar on TotemBarbarian5Lvl" or str(actoid2) == "Morningstar on TotemBarbarian5Lvl"
        assert str(actoid1) == "Hasted Morningstar on TotemBarbarian5Lvl" or str(actoid2) == "Hasted Morningstar on TotemBarbarian5Lvl"
        action_resolver.resolve_action(actoid2, test_bugbear)
        actoid3 = get_action(test_bugbear)
        assert str(actoid3) == "None"
    except Exception as e:
        assert False, f"Raised an exception {e}"