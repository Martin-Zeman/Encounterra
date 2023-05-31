import numpy as np
import pytest

from simulator.action_resolver import ActionResolver
from simulator.actions.action_selector import get_action
from simulator.actions.action_types import BonusAction
from simulator.logging.custom_logger import CustomLogger, LogLevel
from simulator.misc import DamageType
from simulator.teams import Teams
from simulator.test.fixtures import test_moon_druid, combatant3, teams, effect_tracker, battle_map
from simulator.utils.utils import preallocate_wildshape_forms


def test_basic_wildshape(battle_map, teams, effect_tracker, test_moon_druid, combatant3):
    """
    We assert the basic functionality of the wildshape ability. The Druid must be able to wildshape and attack.
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

    try:
        actoid1 = get_action(test_moon_druid, battle_map)
        assert str(actoid1) == "Wildshape of MoonDruid into BrownBear"
        action_resolver.resolve_action(actoid1, test_moon_druid)
        actoid2 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid2, test_moon_druid)
        actoid3 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid3, test_moon_druid)
        actoid4 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid4, test_moon_druid)
        actoid5 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid5, test_moon_druid)
        actoid6 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid6, test_moon_druid)
        actoid7 = get_action(test_moon_druid, battle_map)
        assert str(actoid5) == "Bite on Bugbear" or str(actoid6) == "Bite on Bugbear"
        assert str(actoid5) == "Claws on Bugbear" or str(actoid6) == "Claws on Bugbear"
        assert str(actoid7) == "None"
    except Exception as e:
        assert False, f"Raised an exception {e}"



def test_damage_knocks_out_of_wildshape(battle_map, teams, effect_tracker, test_moon_druid, combatant3):
    """
    We assert that damage can knock the druid out of the wildshape and that damage carries over to the original form.
    We also assert that the druid wil attempt to wildshape again after being knocked out the first time.
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

    try:
        actoid1 = get_action(test_moon_druid, battle_map)
        assert test_moon_druid.curr_hp == 42
        assert str(actoid1) == "Wildshape of MoonDruid into BrownBear"
        action_resolver.resolve_action(actoid1, test_moon_druid)
        assert test_moon_druid.get_current_form() is not test_moon_druid
        assert test_moon_druid.current_wildshape_form is not None
        assert test_moon_druid.get_current_form().curr_hp == 34
        test_moon_druid.get_current_form().receive_dmg(35, DamageType.Slashing)
        assert test_moon_druid.get_current_form() is test_moon_druid
        assert test_moon_druid.current_wildshape_form is None
        assert test_moon_druid.curr_hp == 41
        test_moon_druid.new_turn()
        actoid2 = get_action(test_moon_druid, battle_map)
        assert str(actoid2) == "Wildshape of MoonDruid into BrownBear"
        action_resolver.resolve_action(actoid2, test_moon_druid)
        assert test_moon_druid.get_current_form() is not test_moon_druid
        assert test_moon_druid.current_wildshape_form is not None
        assert test_moon_druid.get_current_form().curr_hp == 34
        test_moon_druid.get_current_form().receive_dmg(37, DamageType.Slashing)
        assert test_moon_druid.get_current_form() is test_moon_druid
        assert test_moon_druid.current_wildshape_form is None
        assert test_moon_druid.curr_hp == 38
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_others_can_attack_wildshape(battle_map, teams, effect_tracker, test_moon_druid, combatant3):
    """
    We assert that others can attack a wildshaped druid
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

    try:
        actoid1 = get_action(test_moon_druid, battle_map)
        assert str(actoid1) == "Wildshape of MoonDruid into BrownBear"
        action_resolver.resolve_action(actoid1, test_moon_druid)
        actoid2 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid2, test_moon_druid)
        actoid3 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid3, test_moon_druid)
        actoid4 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid4, test_moon_druid)

        actoid5 = get_action(combatant3, battle_map)
        assert str(actoid5) == "Morningstar on MoonDruid wildshaped into BrownBear"
        action_resolver.resolve_action(actoid5, combatant3)
    except Exception as e:
        assert False, f"Raised an exception {e}"