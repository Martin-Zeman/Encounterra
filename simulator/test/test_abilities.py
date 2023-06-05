import numpy as np
import pytest

from simulator.abilities.wildshape import WildshapeFactory
from simulator.action_resolver import ActionResolver
from simulator.actions.action_selector import get_action
from simulator.actions.action_types import BonusAction
from simulator.battle_map import Terrain
from simulator.combatants.dire_wolf import DireWolf
from simulator.combatants.giant_constrictor_snake import GiantConstrictorSnake
from simulator.logging.custom_logger import CustomLogger, LogLevel
from simulator.misc import DamageType
from simulator.teams import Teams
from simulator.test.fixtures import test_moon_druid, test_bugbear, teams, effect_tracker, battle_map
from simulator.utils.utils import preallocate_wildshape_forms


def test_basic_wildshape(battle_map, teams, effect_tracker, test_moon_druid, test_bugbear):
    """
    We assert the basic functionality of the wildshape ability. The Druid must be able to wildshape and attack.
    """
    CustomLogger(LogLevel.WARNING)

    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(test_moon_druid, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([0, 0]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 4]))  # Have to set it for fireball placement
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [test_moon_druid, test_bugbear]
    test_moon_druid.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid, BonusAction.MOON_WILDSHAPE, test_moon_druid.wildshape_factory[1])
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)

    try:
        actoid1 = get_action(test_moon_druid, battle_map)
        assert str(actoid1) == "Wildshape of MoonDruid5Lvl into BrownBear"
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
        assert str(actoid4) == "BrownBear Bite on Bugbear" or str(actoid5) == "BrownBear Bite on Bugbear"
        assert str(actoid4) == "BrownBear Claws on Bugbear" or str(actoid5) == "BrownBear Claws on Bugbear"
        assert str(actoid6) == "None"
    except Exception as e:
        assert False, f"Raised an exception {e}"



def test_damage_knocks_out_of_wildshape(battle_map, teams, effect_tracker, test_moon_druid, test_bugbear):
    """
    We assert that damage can knock the druid out of the wildshape and that damage carries over to the original form.
    We also assert that the druid wil attempt to wildshape again after being knocked out the first time. Also that the druid
    canot wildshape a third time.
    """
    CustomLogger(LogLevel.WARNING)

    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(test_moon_druid, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([0, 0]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 4]))  # Have to set it for fireball placement
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [test_moon_druid, test_bugbear]
    test_moon_druid.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid, BonusAction.MOON_WILDSHAPE, test_moon_druid.wildshape_factory[1])
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)

    try:
        actoid1 = get_action(test_moon_druid, battle_map)
        assert test_moon_druid.curr_hp == 42
        assert str(actoid1) == "Wildshape of MoonDruid5Lvl into BrownBear"
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
        assert str(actoid2) == "Wildshape of MoonDruid5Lvl into BrownBear"
        action_resolver.resolve_action(actoid2, test_moon_druid)
        assert test_moon_druid.get_current_form() is not test_moon_druid
        assert test_moon_druid.current_wildshape_form is not None
        assert test_moon_druid.get_current_form().curr_hp == 34
        test_moon_druid.get_current_form().receive_dmg(37, DamageType.Slashing)
        assert test_moon_druid.get_current_form() is test_moon_druid
        assert test_moon_druid.current_wildshape_form is None
        assert test_moon_druid.curr_hp == 38
        actoid3 = get_action(test_moon_druid, battle_map)
        assert not str(actoid3).startswith("Wildshape")
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_others_can_attack_wildshape(battle_map, teams, effect_tracker, test_moon_druid, test_bugbear):
    """
    We assert that others can attack a wildshaped druid
    once.
    """
    CustomLogger(LogLevel.WARNING)

    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(test_moon_druid, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([0, 0]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 4]))  # Have to set it for fireball placement
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [test_moon_druid, test_bugbear]
    test_moon_druid.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid, BonusAction.MOON_WILDSHAPE, test_moon_druid.wildshape_factory[1])
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)

    try:
        actoid1 = get_action(test_moon_druid, battle_map)
        assert str(actoid1) == "Wildshape of MoonDruid5Lvl into BrownBear"
        action_resolver.resolve_action(actoid1, test_moon_druid)
        actoid2 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid2, test_moon_druid)
        actoid3 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid3, test_moon_druid)
        actoid4 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid4, test_moon_druid)

        actoid5 = get_action(test_bugbear, battle_map)
        assert str(actoid5) == "Morningstar on MoonDruid5Lvl wildshaped into BrownBear"
        action_resolver.resolve_action(actoid5, test_bugbear)
    except Exception as e:
        assert False, f"Raised an exception {e}"



def test_wilshape_get_eligible_coords(battle_map, teams, effect_tracker, test_moon_druid, test_bugbear):
    """
    We make sure there's a clearing in the terrain which the giant form fits into. It starts at root coordinate [9, 8].
    """
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(test_moon_druid, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    battle_map.place_circular_element(np.array([1, 13]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([5, 13]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([10, 13]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([13, 13]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([13, 9]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([7, 9]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([4, 9]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([1, 9]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([1, 13]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([11, 4]), Terrain.IMPASSABLE_TERRAIN, radius=3)
    battle_map.place_circular_element(np.array([3, 4]), Terrain.IMPASSABLE_TERRAIN, radius=4)
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([10, 10]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([5, 11]))
    battle_map.build_adjacency_matrix()
    distances, shortest_paths = battle_map.calc_dijkstra(test_moon_druid)
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    test_moon_druid.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid, BonusAction.MOON_WILDSHAPE,
                                                                            test_moon_druid.wildshape_factory[1])

    wsf = WildshapeFactory(test_moon_druid, BonusAction.MOON_WILDSHAPE)
    ws = wsf.create(GiantConstrictorSnake)
    coords = ws.get_eligible_coords(battle_map, distances, shortest_paths)
    assert coords == [(10, 10)]