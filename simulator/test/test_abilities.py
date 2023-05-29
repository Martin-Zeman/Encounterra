import numpy as np
import pytest

from simulator.action_resolver import ActionResolver
from simulator.actions.action_selector import get_action
from simulator.actions.action_types import BonusAction
from simulator.logging.custom_logger import CustomLogger, LogLevel
from simulator.teams import Teams
from simulator.test.fixtures import test_moon_druid, combatant3, teams, effect_tracker, battle_map
from simulator.utils.utils import preallocate_wildshape_forms


def test_wildshape(battle_map, teams, effect_tracker, test_moon_druid, combatant3):
    """
    We assert that a hasted bugbear utilizes both its regular attack and hasted attack independently, although each attack must be used
    once.
    """
    CustomLogger(LogLevel.WARNING)

    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(test_moon_druid, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(combatant3, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([0, 0]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(combatant3, np.array([4, 4]))  # Have to set it for fireball placement
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [test_moon_druid, combatant3]
    test_moon_druid.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid, BonusAction.MOON_WILDSHAPE, test_moon_druid.wildshape_factory[1])
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)

    actoid1 = get_action(test_moon_druid, battle_map)
    action_resolver.resolve_action(actoid1, test_moon_druid)
    actoid2 = get_action(test_moon_druid, battle_map)
    action_resolver.resolve_action(actoid2, test_moon_druid)
    actoid3 = get_action(test_moon_druid, battle_map)
    action_resolver.resolve_action(actoid3, test_moon_druid)

    # try:
    #     hf = HasteFactory(Action.HASTE, combatant1, effect_tracker)
    #     haste = hf.create(combatant3)
    #     action_resolver.resolve_action(haste, combatant1)
    #
    #     actoid1 = get_action(combatant3, battle_map)
    #     action_resolver.resolve_action(actoid1, combatant3)
    #     actoid2 = get_action(combatant3, battle_map)
    #     assert str(actoid1) == "Morningstar on TotemBarbarian5Lvl" or str(actoid2) == "Morningstar on TotemBarbarian5Lvl"
    #     assert str(actoid1) == "Hasted Morningstar on TotemBarbarian5Lvl" or str(actoid2) == "Hasted Morningstar on TotemBarbarian5Lvl"
    #     action_resolver.resolve_action(actoid2, combatant3)
    #     actoid3 = get_action(combatant3, battle_map)
    #     assert str(actoid3) == "None"
    # except Exception as e:
    #     assert False, f"Raised an exception {e}"