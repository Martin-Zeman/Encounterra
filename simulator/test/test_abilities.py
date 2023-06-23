import copy

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
    test_moon_druid.is_concentrating = True  # This way we exclude all the concentration spells from the selection

    try:
        actoid1 = get_action(test_moon_druid, battle_map)
        assert str(actoid1) == "Wildshape of MoonDruid5Lvl into GiantToad"
        action_resolver.resolve_action(actoid1, test_moon_druid)
        actoid2 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid2, test_moon_druid)
        actoid3 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid3, test_moon_druid)
        actoid4 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid4, test_moon_druid)
        actoid5 = get_action(test_moon_druid, battle_map)
        assert str(actoid4) == "GiantToad Bite on Bugbear"
        assert str(actoid5) == "None"
    except Exception as e:
        assert False, f"Raised an exception {e}"

def test_wildshape_with_concentration_spell(battle_map, teams, effect_tracker, test_moon_druid, test_bugbear):
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
    test_bugbear.curr_hp = 1000  # Give the target a bunch of HP to make sure it doesn't die

    try:
        actoid1 = get_action(test_moon_druid, battle_map)
        assert str(actoid1).startswith("Flaming Sphere")
        action_resolver.resolve_action(actoid1, test_moon_druid)
        actoid2 = get_action(test_moon_druid, battle_map)
        assert str(actoid2) == "Wildshape of MoonDruid5Lvl into GiantToad"
        action_resolver.resolve_action(actoid2, test_moon_druid)
        actoid3 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid3, test_moon_druid)
        assert str(actoid3) == "[1 1]"
        actoid4 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid4, test_moon_druid)
        assert str(actoid4) == "[1 1]"
        test_moon_druid.new_turn()
        actoid5 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid5, test_moon_druid)
        actoid6 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid6, test_moon_druid)
        actoid7 = get_action(test_moon_druid, battle_map)
        assert str(actoid5) == "GiantToad Bite on Bugbear" or str(actoid6) == "GiantToad Bite on Bugbear"
        assert str(actoid5) == "Flaming Sphere Ram into Bugbear" or str(actoid6) == "Flaming Sphere Ram into Bugbear"
        assert str(actoid7) == "None"
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_movement_before_wildshape_with_concentration_spell(battle_map, teams, effect_tracker, test_moon_druid, test_bugbear):
    """
    We assert that action plan combination works with a concentration spell even when the druid first has to move in order to wildshape.
    There's a sort of a tunnel the druid first needs to get out of.
    """
    CustomLogger(LogLevel.WARNING)

    battle_map.set_effect_tracker(effect_tracker)
    battle_map.place_circular_element(np.array([0, 0]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([0, 1]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([0, 2]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([0, 3]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([0, 4]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([2, 0]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([2, 1]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([2, 2]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([1, 4]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([2, 4]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([3, 4]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([3, 2]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(test_moon_druid, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([1, 0]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(test_bugbear, np.array([7, 6]))  # Have to set it for fireball placement
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [test_moon_druid, test_bugbear]
    test_moon_druid.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid, BonusAction.MOON_WILDSHAPE, test_moon_druid.wildshape_factory[1])
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)
    test_bugbear.curr_hp = 1000  # Give the target a bunch of HP to make sure it doesn't die

    try:
        actoid1 = get_action(test_moon_druid, battle_map)
        assert str(actoid1) =="[0 1]"
        action_resolver.resolve_action(actoid1, test_moon_druid)
        actoid2 = get_action(test_moon_druid, battle_map)
        assert str(actoid2) == "[0 1]"
        action_resolver.resolve_action(actoid2, test_moon_druid)
        actoid3 = get_action(test_moon_druid, battle_map)
        assert str(actoid3) == "[1 1]"
        action_resolver.resolve_action(actoid3, test_moon_druid)
        actoid4 = get_action(test_moon_druid, battle_map)
        assert str(actoid4) == "[1 0]"
        action_resolver.resolve_action(actoid4, test_moon_druid)
        actoid5 = get_action(test_moon_druid, battle_map)
        assert str(actoid5) == "[1 1]" or str(actoid5) == "[1 0]" or str(actoid5) == '[ 1 -1]'
        action_resolver.resolve_action(actoid5, test_moon_druid)

        actoid7 = get_action(test_moon_druid, battle_map)
        assert str(actoid7).startswith("Flaming Sphere")
        action_resolver.resolve_action(actoid7, test_moon_druid)
        actoid8 = get_action(test_moon_druid, battle_map)
        assert str(actoid8) == "Wildshape of MoonDruid5Lvl into GiantToad"
        action_resolver.resolve_action(actoid8, test_moon_druid)
        actoid9 = get_action(test_moon_druid, battle_map)
        assert str(actoid9) == "None"
        test_moon_druid.new_turn()

        actoid10 = get_action(test_moon_druid, battle_map)
        print()
        print(str(actoid7))
        print("actoid10 " + str(actoid10))
        action_resolver.resolve_action(actoid10, test_moon_druid)
        actoid11 = get_action(test_moon_druid, battle_map)
        print("actoid11 " + str(actoid11))
        action_resolver.resolve_action(actoid11, test_moon_druid)
        actoid12 = get_action(test_moon_druid, battle_map)
        print("actoid12 " + str(actoid12))
        action_resolver.resolve_action(actoid12, test_moon_druid)
        actoid13 = get_action(test_moon_druid, battle_map)
        print("actoid13 " + str(actoid13))
        action_resolver.resolve_action(actoid13, test_moon_druid)
        actoid14 = get_action(test_moon_druid, battle_map)
        print("actoid14 " + str(actoid14))
        action_resolver.resolve_action(actoid14, test_moon_druid)
        actoid15 = get_action(test_moon_druid, battle_map)
        print("actoid15 " + str(actoid15))
        action_resolver.resolve_action(actoid15, test_moon_druid)
        # We don't know exactly where the Flaming sphere is gonna be placed so the druid might need to maneuver around the target out of its range
        assert str(actoid12) == 'GiantToad Bite on Bugbear' or str(actoid13) == 'GiantToad Bite on Bugbear' or str(actoid14) == 'GiantToad Bite on Bugbear' or str(actoid15) == 'GiantToad Bite on Bugbear'
        assert str(actoid12) == 'Flaming Sphere Ram into Bugbear' or str(actoid13) == 'Flaming Sphere Ram into Bugbear' or str(actoid14) == 'Flaming Sphere Ram into Bugbear' or str(actoid15) == 'Flaming Sphere Ram into Bugbear'
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
    test_moon_druid.is_concentrating = True  # This way we exclude all the concentration spells from the selection

    try:
        actoid1 = get_action(test_moon_druid, battle_map)
        assert test_moon_druid.curr_hp == 42
        assert str(actoid1) == "Wildshape of MoonDruid5Lvl into GiantToad"
        action_resolver.resolve_action(actoid1, test_moon_druid)
        assert test_moon_druid.get_current_form() is not test_moon_druid
        assert test_moon_druid.current_wildshape_form is not None
        assert test_moon_druid.get_current_form().curr_hp == 39
        test_moon_druid.get_current_form().receive_dmg(40, DamageType.Slashing)
        assert test_moon_druid.get_current_form() is test_moon_druid
        assert test_moon_druid.current_wildshape_form is None
        assert test_moon_druid.curr_hp == 41
        test_moon_druid.new_turn()
        actoid2 = get_action(test_moon_druid, battle_map)
        assert str(actoid2) == "Wildshape of MoonDruid5Lvl into GiantToad"
        action_resolver.resolve_action(actoid2, test_moon_druid)
        assert test_moon_druid.get_current_form() is not test_moon_druid
        assert test_moon_druid.current_wildshape_form is not None
        assert test_moon_druid.get_current_form().curr_hp == 39
        test_moon_druid.get_current_form().receive_dmg(42, DamageType.Slashing)
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
    test_moon_druid.is_concentrating = True  # This way we exclude all the concentration spells from the selection

    try:
        actoid1 = get_action(test_moon_druid, battle_map)
        assert str(actoid1) == "Wildshape of MoonDruid5Lvl into GiantToad"
        action_resolver.resolve_action(actoid1, test_moon_druid)
        actoid2 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid2, test_moon_druid)
        actoid3 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid3, test_moon_druid)
        actoid4 = get_action(test_moon_druid, battle_map)
        action_resolver.resolve_action(actoid4, test_moon_druid)

        actoid5 = get_action(test_bugbear, battle_map)
        assert str(actoid5) == "Morningstar on MoonDruid5Lvl wildshaped into GiantToad"
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
    assert coords == [(9, 9)]

def test_wilshape_copy_two_druids(battle_map, teams, effect_tracker, test_moon_druid, test_bugbear):
    """
    We make sure there's a clearing in the terrain which the giant form fits into. It starts at root coordinate [9, 8].
    """
    test_moon_druid_2 = copy.deepcopy(test_moon_druid)
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
    test_moon_druid_2.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid_2, BonusAction.MOON_WILDSHAPE, test_moon_druid_2.wildshape_factory[1])
    assert test_moon_druid.available_wildshape_forms[0] is not test_moon_druid_2.available_wildshape_forms[0]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)