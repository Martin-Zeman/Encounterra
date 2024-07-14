import copy
import logging
import pstats

import numpy as np
import pytest
import pickle

from simulator.abilities.wildshape import WildshapeFactory
from simulator.action_resolver import ActionResolver
from simulator.actions.action_types import BonusAction, Action, Passive, FreeAction
from simulator.actions.movement import MovementIncrement
from simulator.battle_map import Terrain, Map, _get_cartesian_distance_coords
from simulator.combatants.giant_toad import GiantToad
from simulator.logging.custom_logger import CustomLogger
from simulator.misc import PhaseOfTurn, SkillCheck
from simulator.conditions import Conditions, Condition, ConditionWithDC, is_affected_by, apply_condition, \
    apply_dc_condition
from simulator.resources import ResourceDepletionLevel
from simulator.session import Session
from simulator.spells.fireball import Fireball
from simulator.spells.firebolt import Firebolt
from simulator.spells.flaming_sphere import FlamingSphereFactory
from simulator.spells.haste import HasteFactory
from simulator.spells.spell import SpellStats
from simulator.spells.twinned_firebolt import TwinnedFirebolt
from simulator.teams import Teams
from simulator.test.fixtures import test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, test_totem_barbarian, test_stone_giant,\
    test_ogre, test_moon_druid, test_giant_toad, teams, effect_tracker, battle_map, test_dragonclaw_cultist, test_brown_bear,\
    test_dire_wolf, test_assassin_rogue, test_draconic_sorcerer_3lvl, test_giant_constrictor_snake, test_twig_blight, \
    test_bandit_captain, test_sabertoother_tiger, test_berserker, test_evil_mage, test_commoner, test_fighter_lvl_2, \
    test_battle_master_fighter_lvl_3, test_fighter_lvl_1, test_ghoul, test_skeleton, test_hobgoblin, test_orc, \
    test_assassin_rogue_3lvl
from simulator.actions.action_selector import get_action
from simulator.utils.utils import preallocate_wildshape_forms
import cProfile


def test_error_case_1(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_bugbear):
    """
    This test case is based on a scenario encountered during fuzzy testing. We make sure that test_draconic_sorcerer_5lvl doesn't hit
    itself with a fireball.
    """
    CustomLogger(logging.WARNING)
    battle_map.place_circular_element(np.array([7, 10]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([10, 2]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([3, 2]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([5, 4]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([3, 14]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 13]))  # Have to set it for fireball placement

    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)

    class DummyEffect:
        def deactivate(self):
            test_draconic_sorcerer_5lvl.break_concentration()

        def deactivate_for_combatant(self, combatant):
            assert False

        def is_affecting(self, combatant):
            return False
    dummy_effect = DummyEffect()
    test_draconic_sorcerer_5lvl.concentration_effect = dummy_effect  # Make sure the sorcerer won't opt for Hold Person

    test_draconic_sorcerer_5lvl.shortest_paths_cache = shortest_paths
    action_plan = test_draconic_sorcerer_5lvl.calculate_action_plan(distances, shortest_paths)
    new_coord = copy.copy(battle_map.get_combatant_position(test_draconic_sorcerer_5lvl).get())
    for ba in action_plan:
        new_coord += ba.increment if isinstance(ba, MovementIncrement) else np.array([[0, 0]])
    fireball = action_plan[0] if isinstance(action_plan[0], Fireball) else action_plan[1]
    # Staying still is actually preferable here
    assert _get_cartesian_distance_coords(battle_map.get_combatant_position(test_draconic_sorcerer_5lvl).get(), np.array([fireball.coord])) > SpellStats.TRANSLATE_RADIUS[fireball.factory.target]
    assert isinstance(action_plan[0], Fireball) or isinstance(action_plan[0], Firebolt)
    assert isinstance(action_plan[1], Fireball) or isinstance(action_plan[1], Firebolt)


def test_error_case_2(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_bugbear):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(logging.WARNING)
    test_bugbear_2 = copy.deepcopy(test_bugbear)
    battle_map.place_circular_element(np.array([6, 2]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([14, 0]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([13, 14]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([14, 14]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([9, 4]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([7, 14]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    teams.add_combatant_to_team(test_bugbear_2, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 8]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([1, 9]))
    battle_map.set_combatant_coordinates(test_bugbear_2, np.array([2, 9]))
    battle_map.build_adjacency_matrix()

    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    test_draconic_sorcerer_5lvl.shortest_paths_cache = shortest_paths
    action_plan = test_draconic_sorcerer_5lvl.calculate_action_plan(distances, shortest_paths)
    try:
        fireball = next(a for a in action_plan if isinstance(a, Fireball))
        assert _get_cartesian_distance_coords(battle_map.get_combatant_position(test_draconic_sorcerer_5lvl).get(), np.array([fireball.coord])) > SpellStats.TRANSLATE_RADIUS[fireball.factory.target]
        assert _get_cartesian_distance_coords(battle_map.get_combatant_position(test_bugbear).get(), np.array([fireball.coord])) <= SpellStats.TRANSLATE_RADIUS[fireball.factory.target]
        assert _get_cartesian_distance_coords(battle_map.get_combatant_position(test_bugbear_2).get(), np.array([fireball.coord])) <= SpellStats.TRANSLATE_RADIUS[fireball.factory.target]
    except StopIteration:
        assert False, "No Fireball planned"
    try:
        next(a for a in action_plan if isinstance(a, TwinnedFirebolt))
    except StopIteration:
        assert False, "No TwinnedFirebolt planned"


def test_error_case_3(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_bugbear, test_totem_barbarian, test_stone_giant, test_ogre):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(logging.WARNING)
    combatant7 = copy.deepcopy(test_bugbear)
    battle_map.place_circular_element(np.array([6, 2]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([14, 8]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([1, 3]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([1, 8]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_draconic_sorcerer_5lvl, test_bugbear, test_totem_barbarian, test_stone_giant, test_ogre, combatant7]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.RED)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.RED)
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.RED)
    teams.add_combatant_to_team(test_ogre, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant7, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([14, 13]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([3, 11]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([3, 12]))
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([0, 11]))
    battle_map.set_combatant_coordinates(test_ogre, np.array([3, 9]))
    battle_map.set_combatant_coordinates(combatant7, np.array([9, 12]))
    battle_map.build_adjacency_matrix()

    try:
        actoid1 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid1, test_draconic_sorcerer_5lvl)
        actoid2 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid2, test_draconic_sorcerer_5lvl)
        actoid3 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid3, test_draconic_sorcerer_5lvl)
        actoid4 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid4, test_draconic_sorcerer_5lvl)
        actoid5 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid5, test_draconic_sorcerer_5lvl)
        actoid6 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid6, test_draconic_sorcerer_5lvl)
        actoid7 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid7, test_draconic_sorcerer_5lvl)
        actoid8 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid8, test_draconic_sorcerer_5lvl)
        actoid9 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid9, test_draconic_sorcerer_5lvl)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_4(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_totem_barbarian, test_stone_giant):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(logging.WARNING)
    test_draconic_sorcerer_5lvl_2 = copy.deepcopy(test_draconic_sorcerer_5lvl)
    battle_map.place_circular_element(np.array([2, 13]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([3, 7]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([4, 5]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([5, 1]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_draconic_sorcerer_5lvl, test_totem_barbarian, test_stone_giant, test_draconic_sorcerer_5lvl_2]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.RED)
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.RED)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl_2, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([9, 13]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([10, 9]))
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([4, 8]))
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl_2, np.array([7, 8]))
    battle_map.build_adjacency_matrix()

    try:
        # The Danger Zone of the Stone Giant spans the whole map so it doesn't pay off to move and suffer the AoO
    # from ..actions.action_selector import get_action
    # cProfile.runctx('get_action(test_draconic_sorcerer_5lvl)', None, locals(), filename="get_action_stats")
    # p = pstats.Stats("get_action_stats")
    # p.strip_dirs().sort_stats("cumtime").print_stats()

        actoid1 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid1, test_draconic_sorcerer_5lvl)
        actoid2 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid2, test_draconic_sorcerer_5lvl)
        actoid3 = get_action(test_draconic_sorcerer_5lvl)
        assert actoid3 is None
    except Exception as e:
        assert False, f"Raised an exception {e}"


@pytest.mark.skip(reason="Takes too long")
def test_error_case_5(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_goblin, test_totem_barbarian, test_stone_giant, test_ogre):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(logging.WARNING)
    test_draconic_sorcerer_5lvl_2 = copy.deepcopy(test_draconic_sorcerer_5lvl)
    battle_map.place_circular_element(np.array([4, 13]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([8, 10]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([13, 8]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_draconic_sorcerer_5lvl, test_goblin, test_totem_barbarian, test_stone_giant, test_ogre, test_draconic_sorcerer_5lvl_2]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.RED)
    teams.add_combatant_to_team(test_ogre, Teams.Color.RED)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl_2, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([14, 14]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([9, 14]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([10, 13]))
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([0, 8]))
    battle_map.set_combatant_coordinates(test_ogre, np.array([10, 10]))
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl_2, np.array([7, 8]))
    battle_map.build_adjacency_matrix()

    try:
        actoid1 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid1, test_draconic_sorcerer_5lvl)
        actoid2 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid2, test_draconic_sorcerer_5lvl)
        actoid3 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid3, test_draconic_sorcerer_5lvl)
        actoid4 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid4, test_draconic_sorcerer_5lvl)
        actoid5 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid5, test_draconic_sorcerer_5lvl)
        actoid6 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid6, test_draconic_sorcerer_5lvl)
        actoid7 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid7, test_draconic_sorcerer_5lvl)
        actoid8 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid8, test_draconic_sorcerer_5lvl)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_6(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_bugbear, test_totem_barbarian, test_ogre):
    """
    This test case is based on a scenario encountered during fuzzy testing. The purpose of this test is to make sure we don't enter
    into an endless recursion via the Barbarian's Reckless Attack.
    """
    CustomLogger(logging.WARNING)
    combatant7 = copy.deepcopy(test_totem_barbarian)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_bugbear, test_totem_barbarian, test_ogre, combatant7]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_ogre, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant7, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 5]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([14, 14]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([9, 14]))
    battle_map.set_combatant_coordinates(test_ogre, np.array([10, 13]))
    battle_map.set_combatant_coordinates(combatant7, np.array([0, 8]))
    battle_map.build_adjacency_matrix()

    try:
        actoid1 = get_action(test_totem_barbarian)
        action_resolver.resolve_action(actoid1, test_totem_barbarian)
        actoid2 = get_action(test_totem_barbarian)
        action_resolver.resolve_action(actoid2, test_totem_barbarian)
        actoid3 = get_action(test_totem_barbarian)
        action_resolver.resolve_action(actoid3, test_totem_barbarian)
        actoid4 = get_action(test_totem_barbarian)
        action_resolver.resolve_action(actoid4, test_totem_barbarian)
        actoid5 = get_action(test_totem_barbarian)
        action_resolver.resolve_action(actoid5, test_totem_barbarian)
        actoid6 = get_action(test_totem_barbarian)
        action_resolver.resolve_action(actoid6, test_totem_barbarian)
        actoid7 = get_action(test_totem_barbarian)
        action_resolver.resolve_action(actoid7, test_totem_barbarian)
        actoid8 = get_action(test_totem_barbarian)
        action_resolver.resolve_action(actoid8, test_totem_barbarian)
        actoid9 = get_action(test_totem_barbarian)
        action_resolver.resolve_action(actoid9, test_totem_barbarian)
        actoid10 = get_action(test_totem_barbarian)
        action_resolver.resolve_action(actoid10, test_totem_barbarian)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_7(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_goblin, test_totem_barbarian):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(logging.WARNING)
    test_draconic_sorcerer_5lvl_2 = copy.deepcopy(test_draconic_sorcerer_5lvl)
    battle_map.place_circular_element(np.array([0, 6]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([11, 13]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([13, 1]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([10, 12]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_draconic_sorcerer_5lvl, test_totem_barbarian, test_stone_giant, test_draconic_sorcerer_5lvl_2]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([9, 13]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([10, 9]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([4, 8]))
    battle_map.build_adjacency_matrix()

    try:
        actoid1 = get_action(test_goblin)
        action_resolver.resolve_action(actoid1, test_goblin)
        actoid2 = get_action(test_goblin)
        action_resolver.resolve_action(actoid2, test_goblin)
        actoid3 = get_action(test_goblin)
        action_resolver.resolve_action(actoid3, test_goblin)
        actoid4 = get_action(test_goblin)
        action_resolver.resolve_action(actoid4, test_goblin)
        actoid5 = get_action(test_goblin)
        action_resolver.resolve_action(actoid5, test_goblin)
        actoid6 = get_action(test_goblin)
        action_resolver.resolve_action(actoid6, test_goblin)

        actoid1 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid1, test_draconic_sorcerer_5lvl)
        actoid2 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid2, test_draconic_sorcerer_5lvl)
        actoid3 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid3, test_draconic_sorcerer_5lvl)
        actoid4 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid4, test_draconic_sorcerer_5lvl)
        actoid5 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid5, test_draconic_sorcerer_5lvl)
        actoid6 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid6, test_draconic_sorcerer_5lvl)
        actoid7 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid7, test_draconic_sorcerer_5lvl)
        actoid8 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid8, test_draconic_sorcerer_5lvl)

        actoid1 = get_action(test_totem_barbarian)
        action_resolver.resolve_action(actoid1, test_totem_barbarian)
        actoid2 = get_action(test_totem_barbarian)
        action_resolver.resolve_action(actoid2, test_totem_barbarian)
        actoid3 = get_action(test_totem_barbarian)
        action_resolver.resolve_action(actoid3, test_totem_barbarian)
        actoid4 = get_action(test_totem_barbarian)
        action_resolver.resolve_action(actoid4, test_totem_barbarian)
        actoid5 = get_action(test_totem_barbarian)
        action_resolver.resolve_action(actoid5, test_totem_barbarian)
        actoid6 = get_action(test_totem_barbarian)
        action_resolver.resolve_action(actoid6, test_totem_barbarian)
        actoid7 = get_action(test_totem_barbarian)
        action_resolver.resolve_action(actoid7, test_totem_barbarian)
        actoid8 = get_action(test_totem_barbarian)
        action_resolver.resolve_action(actoid8, test_totem_barbarian)
        actoid9 = get_action(test_totem_barbarian)
        action_resolver.resolve_action(actoid9, test_totem_barbarian)
        actoid10 = get_action(test_totem_barbarian)
        action_resolver.resolve_action(actoid10, test_totem_barbarian)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_8(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_stone_giant, test_ogre):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(logging.WARNING)
    combatant7 = copy.deepcopy(test_draconic_sorcerer_5lvl)
    battle_map.place_circular_element(np.array([4, 12]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([0, 1]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([6, 12]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([14, 13]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_draconic_sorcerer_5lvl, test_stone_giant, test_ogre, combatant7]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.RED)
    teams.add_combatant_to_team(test_ogre, Teams.Color.RED)
    teams.add_combatant_to_team(combatant7, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([10, 10]))
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([0, 12]))
    battle_map.set_combatant_coordinates(test_ogre, np.array([9, 13]))
    battle_map.set_combatant_coordinates(combatant7, np.array([8, 13]))
    battle_map.build_adjacency_matrix()

    try:
        actoid1 = get_action(combatant7)
        action_resolver.resolve_action(actoid1, combatant7)
        actoid2 = get_action(combatant7)
        action_resolver.resolve_action(actoid2, combatant7)
        actoid3 = get_action(combatant7)
        action_resolver.resolve_action(actoid3, combatant7)
        actoid4 = get_action(combatant7)
        action_resolver.resolve_action(actoid4, combatant7)
        actoid5 = get_action(combatant7)
        action_resolver.resolve_action(actoid5, combatant7)
        actoid6 = get_action(combatant7)
        action_resolver.resolve_action(actoid6, combatant7)
        actoid7 = get_action(combatant7)
        action_resolver.resolve_action(actoid7, combatant7)
        actoid8 = get_action(combatant7)
        action_resolver.resolve_action(actoid8, combatant7)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_9(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_stone_giant, test_ogre):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(logging.WARNING)
    combatant7 = copy.deepcopy(test_stone_giant)
    combatant8 = copy.deepcopy(test_ogre)
    battle_map.place_circular_element(np.array([10, 10]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([13, 14]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([6, 0]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_draconic_sorcerer_5lvl, test_stone_giant, test_ogre, combatant7, combatant8]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_ogre, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant7, Teams.Color.RED)
    teams.add_combatant_to_team(combatant8, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([3, 5]))
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([12, 10]))
    battle_map.set_combatant_coordinates(test_ogre, np.array([1, 10]))
    battle_map.set_combatant_coordinates(combatant7, np.array([3, 8]))
    battle_map.set_combatant_coordinates(combatant8, np.array([12, 8]))
    battle_map.build_adjacency_matrix()

    try:
        actoid1 = get_action(test_stone_giant)
        action_resolver.resolve_action(actoid1, test_stone_giant)
        actoid2 = get_action(test_stone_giant)
        action_resolver.resolve_action(actoid2, test_stone_giant)

        actoid3 = get_action(combatant7)
        action_resolver.resolve_action(actoid3, combatant7)

        actoid4 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid4, test_draconic_sorcerer_5lvl)
        actoid5 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid5, test_draconic_sorcerer_5lvl)

    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_10(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_goblin, test_stone_giant):
    """
    This test case is based on a scenario encountered during fuzzy testing. Here the sorcerer is out of 3rd level spellslots.
    """
    CustomLogger(logging.WARNING)
    battle_map.place_circular_element(np.array([3, 3]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([4, 13]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([5, 4]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([13, 1]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_draconic_sorcerer_5lvl, test_stone_giant]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 3]))
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([3, 6]))
    battle_map.build_adjacency_matrix()
    test_stone_giant.curr_hp = 52
    test_draconic_sorcerer_5lvl.spellslots.use_resource(level=3)
    test_draconic_sorcerer_5lvl.spellslots.use_resource(level=1)
    test_draconic_sorcerer_5lvl.spellslots.use_resource(level=1)
    test_draconic_sorcerer_5lvl.spellslots.use_resource(level=3)
    test_draconic_sorcerer_5lvl.resources[Passive.METAMAGIC].use_resource(4)

    try:
        actoid1 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid1, test_draconic_sorcerer_5lvl)
        actoid2 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid2, test_draconic_sorcerer_5lvl)
        actoid3 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid3, test_draconic_sorcerer_5lvl)
        actoid4 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid4, test_draconic_sorcerer_5lvl)
        actoid5 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid5, test_draconic_sorcerer_5lvl)
        actoid6 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid6, test_draconic_sorcerer_5lvl)
        actoid7 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid7, test_draconic_sorcerer_5lvl)
        actoid8 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid8, test_draconic_sorcerer_5lvl)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_11(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_totem_barbarian, test_stone_giant, test_ogre):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(logging.WARNING)
    combatant7 = copy.deepcopy(test_draconic_sorcerer_5lvl)
    combatant8 = copy.deepcopy(test_stone_giant)
    battle_map.place_circular_element(np.array([2, 4]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([7, 3]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([4, 1]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([9, 9]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_draconic_sorcerer_5lvl, test_totem_barbarian, test_stone_giant, test_ogre, combatant7, combatant8]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.RED)
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_ogre, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant7, Teams.Color.RED)
    teams.add_combatant_to_team(combatant8, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([7, 8]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([6, 12]))
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([9, 9]))
    battle_map.set_combatant_coordinates(test_ogre, np.array([6, 10]))
    battle_map.set_combatant_coordinates(combatant7, np.array([9, 12]))
    battle_map.set_combatant_coordinates(combatant8, np.array([3, 10]))
    battle_map.build_adjacency_matrix()

    test_totem_barbarian.resources[BonusAction.TOTEM_RAGE].use_resource()
    test_ogre.curr_hp -= 32
    combatant7.curr_hp -= 4
    combatant7.spellslots.use_resource(level=3)
    combatant7.resources[Passive.METAMAGIC].use_resource(5)

    try:
        actoid1 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid1, test_draconic_sorcerer_5lvl)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_12(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_totem_barbarian, test_stone_giant, test_ogre):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(logging.WARNING)
    combatant7 = copy.deepcopy(test_totem_barbarian)
    battle_map.place_circular_element(np.array([0, 7]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([7, 14]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([1, 10]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([6, 7]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_draconic_sorcerer_5lvl, test_totem_barbarian, test_stone_giant, test_ogre, combatant7]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.RED)
    teams.add_combatant_to_team(test_ogre, Teams.Color.BLUE)
    teams.add_combatant_to_team(combatant7, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([7, 13]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([6, 11]))
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([7, 10]))
    battle_map.set_combatant_coordinates(test_ogre, np.array([10, 9]))
    battle_map.set_combatant_coordinates(combatant7, np.array([6, 12]))
    battle_map.build_adjacency_matrix()

    test_totem_barbarian.curr_hp = 61

    test_draconic_sorcerer_5lvl.curr_hp = 7
    test_draconic_sorcerer_5lvl.spellslots.use_resource(level=3)
    test_draconic_sorcerer_5lvl.spellslots.use_resource(level=3)
    test_draconic_sorcerer_5lvl.spellslots.use_resource(level=1)
    test_draconic_sorcerer_5lvl.spellslots.use_resource(level=1)
    test_draconic_sorcerer_5lvl.resources[Passive.METAMAGIC].use_resource(5)
    apply_condition(test_draconic_sorcerer_5lvl, Condition(Conditions.PRONE, test_stone_giant))

    test_stone_giant.ammo[test_stone_giant.rock[1].name].deplete_resource(ResourceDepletionLevel.FULLY_DEPLETED)
    test_stone_giant.curr_hp = 46
    test_ogre.curr_hp = 45
    combatant7.curr_hp = 36

    try:
        actoid1 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid1, test_draconic_sorcerer_5lvl)
        actoid2 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid2, test_draconic_sorcerer_5lvl)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_13(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_totem_barbarian, test_stone_giant):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(logging.WARNING)
    test_stone_giant_2 = copy.deepcopy(test_stone_giant)
    battle_map.place_circular_element(np.array([1, 3]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([12, 14]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([3, 12]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([9, 11]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_draconic_sorcerer_5lvl, test_totem_barbarian, test_stone_giant, test_stone_giant_2]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.RED)
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_stone_giant_2, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 5]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([4, 6]))
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([1, 10]))
    battle_map.set_combatant_coordinates(test_stone_giant_2, np.array([8, 8]))
    battle_map.build_adjacency_matrix()

    test_draconic_sorcerer_5lvl.curr_hp = 43
    test_draconic_sorcerer_5lvl.spellslots.use_resource(level=3)
    test_draconic_sorcerer_5lvl.spellslots.use_resource(level=3)
    test_draconic_sorcerer_5lvl.spellslots.use_resource(level=1)
    test_draconic_sorcerer_5lvl.resources[Passive.METAMAGIC].use_resource(5)

    try:
        actoid1 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid1, test_draconic_sorcerer_5lvl)
        actoid2 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid2, test_draconic_sorcerer_5lvl)
        actoid3 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid3, test_draconic_sorcerer_5lvl)
        actoid4 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid4, test_draconic_sorcerer_5lvl)
        actoid5 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid5, test_draconic_sorcerer_5lvl)
        actoid6 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid6, test_draconic_sorcerer_5lvl)
        actoid7 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid7, test_draconic_sorcerer_5lvl)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_14(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_stone_giant, test_ogre):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(logging.WARNING)
    battle_map.place_circular_element(np.array([4, 11]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([13, 10]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([10, 13]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([10, 2]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_draconic_sorcerer_5lvl, test_stone_giant, test_ogre]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.RED)
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_ogre, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 14]))
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([0, 10]))
    battle_map.set_combatant_coordinates(test_ogre, np.array([1, 13]))
    battle_map.build_adjacency_matrix()

    test_draconic_sorcerer_5lvl.spellslots.use_resource(level=3)
    test_draconic_sorcerer_5lvl.spellslots.use_resource(level=1)
    test_draconic_sorcerer_5lvl.resources[Passive.METAMAGIC].use_resource(2)

    try:
        actoid1 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid1, test_draconic_sorcerer_5lvl)
        actoid2 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid2, test_draconic_sorcerer_5lvl)
        actoid3 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid3, test_draconic_sorcerer_5lvl)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_15(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_goblin, test_totem_barbarian, test_stone_giant, test_ogre):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    # TODO Why is this not failing?
    CustomLogger(logging.WARNING)
    battle_map.place_circular_element(np.array([0, 12]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([7, 10]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([10, 12]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([13, 6]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_draconic_sorcerer_5lvl, test_goblin, test_totem_barbarian, test_stone_giant, test_ogre]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.RED)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.RED)
    teams.add_combatant_to_team(test_ogre, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([7, 8]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([0, 9]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([8, 7]))
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([8, 12]))
    battle_map.set_combatant_coordinates(test_ogre, np.array([9, 8]))
    battle_map.build_adjacency_matrix()

    test_stone_giant.add_hasted_factories()
    test_stone_giant.has_haste_action = True
    test_draconic_sorcerer_5lvl.spellslots.use_resource(level=3)
    test_draconic_sorcerer_5lvl.spellslots.use_resource(level=3)
    test_draconic_sorcerer_5lvl.spellslots.use_resource(level=1)
    test_draconic_sorcerer_5lvl.resources[Passive.METAMAGIC].use_resource(5)

    try:
        actoid1 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid1, test_draconic_sorcerer_5lvl)
        actoid2 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid2, test_draconic_sorcerer_5lvl)
        actoid3 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid3, test_draconic_sorcerer_5lvl)
        actoid4 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid4, test_draconic_sorcerer_5lvl)
        actoid5 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid5, test_draconic_sorcerer_5lvl)
        actoid6 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid6, test_draconic_sorcerer_5lvl)
        actoid7 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid7, test_draconic_sorcerer_5lvl)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_16(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_goblin, test_stone_giant, test_ogre):
    """
    This test case is based on a scenario encountered during fuzzy testing.
    """
    CustomLogger(logging.WARNING)
    battle_map.place_circular_element(np.array([7, 8]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([6, 13]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([8, 8]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([10, 11]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_draconic_sorcerer_5lvl, test_stone_giant, test_ogre]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.RED)
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_ogre, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 2]))
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([11, 8]))
    battle_map.set_combatant_coordinates(test_ogre, np.array([9, 10]))
    battle_map.build_adjacency_matrix()

    test_draconic_sorcerer_5lvl.spellslots.use_resource(level=3)
    test_draconic_sorcerer_5lvl.spellslots.use_resource(level=3)
    test_draconic_sorcerer_5lvl.resources[Passive.METAMAGIC].use_resource(5)
    apply_condition(test_draconic_sorcerer_5lvl, Condition(Conditions.PRONE, test_stone_giant))

    try:
        actoid1 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid1, test_draconic_sorcerer_5lvl)
        actoid2 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid2, test_draconic_sorcerer_5lvl)
        actoid3 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid3, test_draconic_sorcerer_5lvl)
        actoid4 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid4, test_draconic_sorcerer_5lvl)
        actoid5 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid5, test_draconic_sorcerer_5lvl)
        actoid6 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid6, test_draconic_sorcerer_5lvl)
        actoid7 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid7, test_draconic_sorcerer_5lvl)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_17(battle_map, teams, effect_tracker, test_moon_druid, test_totem_barbarian, test_goblin, test_draconic_sorcerer_5lvl):
    """
    This test case is based on a scenario encountered during fuzzy testing. It makes sure that find_wildshaped_coordinate does its job.
    """
    CustomLogger(logging.WARNING)
    test_totem_barbarian_2 = copy.deepcopy(test_totem_barbarian)
    battle_map.place_circular_element(np.array([6, 14]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    # battle_map.place_circular_element(np.array([0, 5]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([4, 8]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([10, 1]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_moon_druid, test_totem_barbarian, test_goblin, test_draconic_sorcerer_5lvl, test_totem_barbarian_2]
    test_moon_druid.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid, BonusAction.MOON_WILDSHAPE, test_moon_druid.wildshape_factory[1])
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_totem_barbarian_2, Teams.Color.RED)
    teams.add_combatant_to_team(test_moon_druid, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([4, 13]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([6, 10]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([0, 13]))
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([0, 10]))
    battle_map.set_combatant_coordinates(test_totem_barbarian_2, np.array([3, 11]))

    battle_map.build_adjacency_matrix()

    test_moon_druid.has_haste_action = True

    try:
        actoid1 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid1, test_moon_druid)
        actoid2 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid2, test_moon_druid)
        actoid3 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid3, test_moon_druid)
        actoid4 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid4, test_moon_druid)
        actoid5 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid5, test_moon_druid)
        actoid6 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid6, test_moon_druid)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_18(battle_map, teams, effect_tracker, test_moon_druid, test_bugbear, test_goblin):
    """
    This test case is based on a scenario encountered during fuzzy testing. It makes sure that find_wildshaped_coordinate does its job.
    """
    CustomLogger(logging.WARNING)
    battle_map.place_circular_element(np.array([9, 8]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([13, 6]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_moon_druid, test_bugbear, test_goblin]
    test_moon_druid.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid, BonusAction.MOON_WILDSHAPE, test_moon_druid.wildshape_factory[1])
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_moon_druid, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([10, 8]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([11, 8]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([12, 13]))

    battle_map.build_adjacency_matrix()

    test_moon_druid.has_haste_action = True

    try:
        actoid1 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid1, test_moon_druid)
        actoid2 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid2, test_moon_druid)
        actoid3 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid3, test_moon_druid)
        actoid4 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid4, test_moon_druid)
        actoid5 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid5, test_moon_druid)
        actoid6 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid6, test_moon_druid)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_19(battle_map, teams, effect_tracker, test_giant_toad):
    """
    Two giants toads, one of which is hasted. Bite and swallow wasn't being excluded despite not having a grappled target
    """
    # TODO It's not reproducing the error
    test_giant_toad_2 = copy.deepcopy(test_giant_toad)
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_giant_toad, test_giant_toad_2]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_giant_toad, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_giant_toad_2, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_giant_toad, np.array([4, 8]))
    battle_map.set_combatant_coordinates(test_giant_toad_2, np.array([4, 10]))

    battle_map.build_adjacency_matrix()

    test_giant_toad.add_hasted_factories()
    test_giant_toad.has_haste_action = True

    try:
        actoid1 = get_action(test_giant_toad)
        action_resolver.resolve_action(actoid1, test_giant_toad)
        actoid2 = get_action(test_giant_toad)
        action_resolver.resolve_action(actoid2, test_giant_toad)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_20(battle_map, teams, effect_tracker, test_totem_barbarian, test_draconic_sorcerer_5lvl, test_dragonclaw_cultist):
    """
    Aims to solve a bug where hasted actions are modeled incorrectly
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_totem_barbarian, test_draconic_sorcerer_5lvl, test_dragonclaw_cultist]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.RED)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_dragonclaw_cultist, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([13, 9]))
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([10, 14]))
    battle_map.set_combatant_coordinates(test_dragonclaw_cultist, np.array([1, 10]))

    battle_map.build_adjacency_matrix()

    haste_factory = HasteFactory(BonusAction.QUICKENED_HASTE, test_draconic_sorcerer_5lvl, test_draconic_sorcerer_5lvl.spellslots)
    haste = haste_factory.create(test_draconic_sorcerer_5lvl)

    try:
        action_resolver.resolve_action(haste, test_draconic_sorcerer_5lvl)
        actoid1 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid1, test_draconic_sorcerer_5lvl)
        actoid2 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid2, test_draconic_sorcerer_5lvl)
        actoid3 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid3, test_draconic_sorcerer_5lvl)
        actoid4 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid4, test_draconic_sorcerer_5lvl)
        actoid5 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid5, test_draconic_sorcerer_5lvl)
        actoid6 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid6, test_draconic_sorcerer_5lvl)
        actoid7 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid7, test_draconic_sorcerer_5lvl)
        actoid8 = get_action(test_draconic_sorcerer_5lvl)
        action_resolver.resolve_action(actoid8, test_draconic_sorcerer_5lvl)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_21(battle_map, teams, effect_tracker, test_totem_barbarian, test_moon_druid):
    """
    Moon druid being prone, exhausting all their movement but still trying to move.
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_totem_barbarian, test_moon_druid]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.RED)
    teams.add_combatant_to_team(test_moon_druid, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([13, 9]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([0, 9]))
    test_moon_druid.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid, BonusAction.MOON_WILDSHAPE, test_moon_druid.wildshape_factory[1])

    battle_map.build_adjacency_matrix()

    apply_condition(test_moon_druid, Condition(Conditions.PRONE, test_totem_barbarian))

    try:
        actoid1 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid1, test_moon_druid)
        actoid2 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid2, test_moon_druid)
        actoid3 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid3, test_moon_druid)
        actoid4 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid4, test_moon_druid)
        actoid5 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid5, test_moon_druid)
        actoid6 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid6, test_moon_druid)
        actoid7 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid7, test_moon_druid)
        actoid8 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid8, test_moon_druid)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_22(battle_map, teams, effect_tracker, test_totem_barbarian, test_moon_druid, test_draconic_sorcerer_5lvl):
    """
    Hasted moon druid in a Giant Toad form swallows a barbarian
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_totem_barbarian, test_moon_druid, test_draconic_sorcerer_5lvl]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_moon_druid, Teams.Color.RED)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([8, 13]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([7, 13]))
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([8, 8]))
    test_moon_druid.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid, BonusAction.MOON_WILDSHAPE, test_moon_druid.wildshape_factory[1])
    battle_map.build_adjacency_matrix()
    _, shortest_paths = battle_map.calc_dijkstra(test_moon_druid)
    test_moon_druid.shortest_paths_cache = shortest_paths

    ws_factory = WildshapeFactory(test_moon_druid, BonusAction.MOON_WILDSHAPE)
    ws = ws_factory.create(GiantToad)
    fs_factory = FlamingSphereFactory(test_moon_druid.dc, Action.FLAMING_SPHERE, test_moon_druid, test_moon_druid.spellslots)
    fs = fs_factory.create(np.array((6, 13)))
    haste_factory = HasteFactory(BonusAction.QUICKENED_HASTE, test_draconic_sorcerer_5lvl, test_draconic_sorcerer_5lvl.spellslots)
    test_totem_barbarian.ac = 0

    # TODO Failed to reproduce
    try:
        action_resolver.resolve_action(fs, test_moon_druid)
        action_resolver.resolve_action(ws, test_moon_druid)
        test_moon_druid.new_turn()
        bite = test_moon_druid.get_current_form().bite[1].create(test_totem_barbarian)
        action_resolver.resolve_action(bite, test_moon_druid)
        if is_affected_by(test_totem_barbarian, Conditions.GRAPPLED):
            test_moon_druid.new_turn()
            haste = haste_factory.create(test_moon_druid.get_current_form())
            action_resolver.resolve_action(haste, test_draconic_sorcerer_5lvl)
            actoid1 = get_action(test_moon_druid)
            action_resolver.resolve_action(actoid1, test_moon_druid)
            actoid2 = get_action(test_moon_druid)
            action_resolver.resolve_action(actoid2, test_moon_druid)
            actoid3 = get_action(test_moon_druid)
            action_resolver.resolve_action(actoid3, test_moon_druid)
    except Exception as e:
        assert False, f"Raised an exception {e}"

def test_error_case_23(battle_map, teams, effect_tracker, test_ogre, test_stone_giant, test_brown_bear, test_bugbear):
    """
    Ogre tries to go into impassable terrain
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_ogre, test_stone_giant, test_brown_bear, test_bugbear]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_ogre, Teams.Color.RED)
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.RED)
    teams.add_combatant_to_team(test_brown_bear, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_ogre, np.array([5, 8]))
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([6, 11]))
    battle_map.set_combatant_coordinates(test_brown_bear, np.array([0, 9]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([13, 14]))
    battle_map.place_circular_element(np.array([12, 5]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([11, 8]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([12, 3]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([3, 5]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.build_adjacency_matrix()

    try:
        actoid1 = get_action(test_ogre)
        action_resolver.resolve_action(actoid1, test_ogre)
        actoid2 = get_action(test_ogre)
        action_resolver.resolve_action(actoid2, test_ogre)
        actoid3 = get_action(test_ogre)
        action_resolver.resolve_action(actoid3, test_ogre)
        actoid4 = get_action(test_ogre)
        action_resolver.resolve_action(actoid4, test_ogre)
        actoid5 = get_action(test_ogre)
        action_resolver.resolve_action(actoid5, test_ogre)
        actoid6 = get_action(test_ogre)
        action_resolver.resolve_action(actoid6, test_ogre)
        actoid7 = get_action(test_ogre)
        action_resolver.resolve_action(actoid7, test_ogre)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_24(battle_map, teams, effect_tracker, test_moon_druid, test_stone_giant, test_brown_bear, test_bugbear, test_giant_toad, test_ogre):
    """
    Not enough space to wildshape. There was a bug in the plan combination when the druid has no eligible non-wildshape action.
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_moon_druid, test_stone_giant, test_brown_bear, test_bugbear, test_giant_toad, test_ogre]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_moon_druid, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.RED)
    teams.add_combatant_to_team(test_brown_bear, Teams.Color.RED)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    teams.add_combatant_to_team(test_giant_toad, Teams.Color.RED)
    teams.add_combatant_to_team(test_ogre, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([10, 11]))
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([6, 8]))
    battle_map.set_combatant_coordinates(test_brown_bear, np.array([8, 12]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([9, 11]))
    battle_map.set_combatant_coordinates(test_giant_toad, np.array([10, 13]))
    battle_map.set_combatant_coordinates(test_ogre, np.array([11, 11]))
    battle_map.build_adjacency_matrix()
    test_moon_druid.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid, BonusAction.MOON_WILDSHAPE, test_moon_druid.wildshape_factory[1])

    # Make the grapple easy to break out of
    apply_dc_condition(test_moon_druid, ConditionWithDC(Conditions.GRAPPLED | Conditions.RESTRAINED, SkillCheck.ATHLETICS, 1, test_ogre, PhaseOfTurn.ACTION))
    test_ogre.constricted_target = test_moon_druid

    try:
        actoid1 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid1, test_moon_druid)
        actoid2 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid2, test_moon_druid)
        actoid3 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid3, test_moon_druid)
        actoid4 = get_action(test_moon_druid)
        assert str(actoid4).startswith("Wildshape")
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_25(battle_map, teams, effect_tracker, test_dire_wolf, test_giant_toad, test_bugbear, test_totem_barbarian, test_ogre, test_brown_bear):
    """
    Immediate crash when Dire Wolf action planning
    """
    CustomLogger(logging.WARNING)
    test_totem_barbarian_2 = copy.deepcopy(test_totem_barbarian)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_dire_wolf, test_giant_toad, test_bugbear, test_totem_barbarian, test_totem_barbarian_2, test_ogre, test_brown_bear]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)

    battle_map.place_circular_element(np.array([3, 3]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([7, 6]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([0, 12]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([8, 3]), Terrain.DIFFICULT_TERRAIN, radius=1)

    teams.add_combatant_to_team(test_dire_wolf, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_giant_toad, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_totem_barbarian_2, Teams.Color.RED)
    teams.add_combatant_to_team(test_ogre, Teams.Color.RED)
    teams.add_combatant_to_team(test_brown_bear, Teams.Color.RED)

    battle_map.set_combatant_coordinates(test_dire_wolf, np.array([6, 9]))
    battle_map.set_combatant_coordinates(test_giant_toad, np.array([8, 10]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([5, 12]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([10, 14]))
    battle_map.set_combatant_coordinates(test_totem_barbarian_2, np.array([5, 13]))
    battle_map.set_combatant_coordinates(test_ogre, np.array([12, 13]))
    battle_map.set_combatant_coordinates(test_brown_bear, np.array([4, 9]))

    battle_map.build_adjacency_matrix()


    try:
        actoid1 = get_action(test_dire_wolf)
        action_resolver.resolve_action(actoid1, test_dire_wolf)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_26(battle_map, teams, effect_tracker, test_ogre, test_draconic_sorcerer_3lvl):
    """
    Draconic Sorcerer was casting a quickened scorching ray followed by a regular one which is not allowed. This turned
    out to be specific to python version 3.10
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_ogre, test_draconic_sorcerer_3lvl]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)

    battle_map.place_circular_element(np.array([10, 9]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([11, 2]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([6, 5]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([5, 8]), Terrain.DIFFICULT_TERRAIN, radius=0)

    teams.add_combatant_to_team(test_draconic_sorcerer_3lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_ogre, Teams.Color.RED)

    battle_map.set_combatant_coordinates(test_draconic_sorcerer_3lvl, np.array([12, 11]))
    battle_map.set_combatant_coordinates(test_ogre, np.array([10, 12]))

    battle_map.build_adjacency_matrix()

    action_types = [Action.SCORCHING_RAY, BonusAction.QUICKENED_SCORCHING_RAY, Action.HOLD_PERSON]
    actoids = []
    try:
        actoids.append(get_action(test_draconic_sorcerer_3lvl))
        action_resolver.resolve_action(actoids[-1], test_draconic_sorcerer_3lvl)
        actoids.append(get_action(test_draconic_sorcerer_3lvl))
        action_resolver.resolve_action(actoids[-1], test_draconic_sorcerer_3lvl)
        actoids.append(get_action(test_draconic_sorcerer_3lvl))
        action_resolver.resolve_action(actoids[-1], test_draconic_sorcerer_3lvl)
    except Exception as e:
        assert False, f"Raised an exception {e}"
    assert len([1 for a in actoids if a is not None and a.factory.action_type in action_types]) == 1, "Cannot cast two leveled spells in a turn"


def test_error_case_27(battle_map, teams, effect_tracker, test_twig_blight, test_giant_constrictor_snake, test_bandit_captain):
    """
    Error in constrict "AttributeError: 'tuple' object has no attribute 'calculate_threat_to_target'"
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_twig_blight, test_giant_constrictor_snake, test_bandit_captain]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)

    battle_map.place_circular_element(np.array([12, 5]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([6, 4]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([7, 7]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([5, 3]), Terrain.DIFFICULT_TERRAIN, radius=0)

    teams.add_combatant_to_team(test_twig_blight, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_bandit_captain, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_giant_constrictor_snake, Teams.Color.RED)

    battle_map.set_combatant_coordinates(test_twig_blight, np.array([5, 9]))
    battle_map.set_combatant_coordinates(test_bandit_captain, np.array([9, 8]))
    battle_map.set_combatant_coordinates(test_giant_constrictor_snake, np.array([10, 9]))

    battle_map.build_adjacency_matrix()

    actoids = []
    try:
        actoids.append(get_action(test_giant_constrictor_snake))
        action_resolver.resolve_action(actoids[-1], test_giant_constrictor_snake)
        actoids.append(get_action(test_giant_constrictor_snake))
        action_resolver.resolve_action(actoids[-1], test_giant_constrictor_snake)
        actoids.append(get_action(test_giant_constrictor_snake))
        action_resolver.resolve_action(actoids[-1], test_giant_constrictor_snake)
        actoids.append(get_action(test_giant_constrictor_snake))
        action_resolver.resolve_action(actoids[-1], test_giant_constrictor_snake)
        actoids.append(get_action(test_giant_constrictor_snake))
        action_resolver.resolve_action(actoids[-1], test_giant_constrictor_snake)
        actoids.append(get_action(test_giant_constrictor_snake))
        action_resolver.resolve_action(actoids[-1], test_giant_constrictor_snake)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_28(battle_map, teams, effect_tracker, test_moon_druid, test_sabertoother_tiger, test_dire_wolf, test_berserker, test_twig_blight):
    """
    Error in for the Moon Druid "KeyError((<Action.DODGE: 6>, <Encounterra.simulator.actions.dodge.DodgeFactory object at 0x7f8bbb9a5110>))"
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_moon_druid, test_sabertoother_tiger, test_dire_wolf, test_berserker, test_twig_blight]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)

    battle_map.place_circular_element(np.array([7, 11]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([6, 2]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([4, 11]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([9, 4]), Terrain.DIFFICULT_TERRAIN, radius=0)

    teams.add_combatant_to_team(test_moon_druid, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_sabertoother_tiger, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_dire_wolf, Teams.Color.RED)
    teams.add_combatant_to_team(test_berserker, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_twig_blight, Teams.Color.BLUE)

    battle_map.set_combatant_coordinates(test_moon_druid, np.array([5, 14]))
    battle_map.set_combatant_coordinates(test_sabertoother_tiger, np.array([6, 8]))
    battle_map.set_combatant_coordinates(test_dire_wolf, np.array([8, 8]))
    battle_map.set_combatant_coordinates(test_berserker, np.array([2, 8]))
    battle_map.set_combatant_coordinates(test_twig_blight, np.array([13, 10]))
    test_moon_druid.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid, BonusAction.MOON_WILDSHAPE,
                                                                            test_moon_druid.wildshape_factory[1])

    battle_map.build_adjacency_matrix()

    actoids = []
    try:
        actoids.append(get_action(test_moon_druid))
        action_resolver.resolve_action(actoids[-1], test_moon_druid)
        actoids.append(get_action(test_moon_druid))
        action_resolver.resolve_action(actoids[-1], test_moon_druid)
        actoids.append(get_action(test_moon_druid))
        action_resolver.resolve_action(actoids[-1], test_moon_druid)
        actoids.append(get_action(test_moon_druid))
        action_resolver.resolve_action(actoids[-1], test_moon_druid)
        actoids.append(get_action(test_moon_druid))
        action_resolver.resolve_action(actoids[-1], test_moon_druid)
        actoids.append(get_action(test_moon_druid))
        action_resolver.resolve_action(actoids[-1], test_moon_druid)
    except Exception as e:
        assert False, f"Raised an exception {e}"


@pytest.mark.flaky(reruns=3)
def test_error_case_29(battle_map, teams, effect_tracker, test_moon_druid, test_sabertoother_tiger, test_bugbear, test_evil_mage):
    """
    Error in for the Saber-Toother Tiger's "TypeError("unsupported operand type(s) for +: 'Size' and 'int'")"
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    test_sabertoother_tiger_2 = copy.deepcopy(test_sabertoother_tiger)
    test_sabertoother_tiger_2.name = "Saber-Toothed Tiger 2"
    combatants = [test_moon_druid, test_sabertoother_tiger, test_sabertoother_tiger_2, test_bugbear, test_evil_mage]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)

    battle_map.place_circular_element(np.array([9, 12]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([9, 3]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([6, 12]), Terrain.DIFFICULT_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([8, 6]), Terrain.DIFFICULT_TERRAIN, radius=0)

    teams.add_combatant_to_team(test_moon_druid, Teams.Color.RED)
    teams.add_combatant_to_team(test_sabertoother_tiger, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_sabertoother_tiger_2, Teams.Color.RED)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_evil_mage, Teams.Color.RED)

    battle_map.set_combatant_coordinates(test_moon_druid, np.array([13, 11]))
    battle_map.set_combatant_coordinates(test_sabertoother_tiger, np.array([5, 10]))
    battle_map.set_combatant_coordinates(test_sabertoother_tiger_2, np.array([3, 12]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([0, 10]))
    battle_map.set_combatant_coordinates(test_evil_mage, np.array([0, 12]))

    battle_map.build_adjacency_matrix()

    actoids = []
    try:
        actoids.append(get_action(test_sabertoother_tiger))
        action_resolver.resolve_action(actoids[-1], test_sabertoother_tiger)
        actoids.append(get_action(test_sabertoother_tiger))
        action_resolver.resolve_action(actoids[-1], test_sabertoother_tiger)
        actoids.append(get_action(test_sabertoother_tiger))
        action_resolver.resolve_action(actoids[-1], test_sabertoother_tiger)
        actoids.append(get_action(test_sabertoother_tiger))
        action_resolver.resolve_action(actoids[-1], test_sabertoother_tiger)
    except Exception as e:
        assert False, f"Raised an exception {e}"
    assert any([str(a).startswith("Pounce") for a in actoids])


def test_error_case_30(battle_map, teams, effect_tracker, test_battle_master_fighter_lvl_3, test_fighter_lvl_2):
    """
    Battlemaster fighter keeps selecting menacing attacks even when they're not feasible
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_battle_master_fighter_lvl_3, test_fighter_lvl_2]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)

    teams.add_combatant_to_team(test_battle_master_fighter_lvl_3, Teams.Color.RED)
    teams.add_combatant_to_team(test_fighter_lvl_2, Teams.Color.BLUE)

    battle_map.set_combatant_coordinates(test_battle_master_fighter_lvl_3, np.array([14, 10]))
    battle_map.set_combatant_coordinates(test_fighter_lvl_2, np.array([2, 10]))

    test_battle_master_fighter_lvl_3.curr_hp = 17
    test_battle_master_fighter_lvl_3.resources[Passive.BATTLE_MASTER_MANEUVERS].use_resource()
    test_battle_master_fighter_lvl_3.resources[Passive.BATTLE_MASTER_MANEUVERS].use_resource()
    test_battle_master_fighter_lvl_3.resources[Passive.BATTLE_MASTER_MANEUVERS].use_resource()
    test_battle_master_fighter_lvl_3.resources[Passive.BATTLE_MASTER_MANEUVERS].use_resource()
    test_battle_master_fighter_lvl_3.resources[FreeAction.ACTION_SURGE].use_resource()
    test_battle_master_fighter_lvl_3.ammo["Menacing Handaxe"].use_resource()
    test_fighter_lvl_2.ammo["Handaxe"].use_resource()
    test_fighter_lvl_2.ammo["Handaxe"].use_resource()

    battle_map.build_adjacency_matrix()

    actoids = []
    try:
        actoids.append(get_action(test_battle_master_fighter_lvl_3))
        action_resolver.resolve_action(actoids[-1], test_battle_master_fighter_lvl_3)
        actoids.append(get_action(test_battle_master_fighter_lvl_3))
        action_resolver.resolve_action(actoids[-1], test_battle_master_fighter_lvl_3)
        actoids.append(get_action(test_battle_master_fighter_lvl_3))
        action_resolver.resolve_action(actoids[-1], test_battle_master_fighter_lvl_3)
    except Exception as e:
        assert False, f"Raised an exception {e}"
    assert not any(["Menacing Handaxe" in str(a) for a in actoids])


def test_error_case_31(battle_map, teams, effect_tracker, test_battle_master_fighter_lvl_3, test_fighter_lvl_1, test_fighter_lvl_2):
    """
    Trying to understand why the Battlemaster wouldn't move the first turn. This lead to the implementation of the
    LOCATION_INDEPENDENT actoid flag.
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_battle_master_fighter_lvl_3, test_fighter_lvl_2, test_fighter_lvl_1]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)

    teams.add_combatant_to_team(test_battle_master_fighter_lvl_3, Teams.Color.RED)
    teams.add_combatant_to_team(test_fighter_lvl_1, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_fighter_lvl_2, Teams.Color.BLUE)

    battle_map.set_combatant_coordinates(test_battle_master_fighter_lvl_3, np.array([0, 12]))
    battle_map.set_combatant_coordinates(test_fighter_lvl_1, np.array([13, 9]))
    battle_map.set_combatant_coordinates(test_fighter_lvl_2, np.array([2, 11]))

    battle_map.build_adjacency_matrix()

    actoids = []
    try:
        actoids.append(get_action(test_battle_master_fighter_lvl_3))
        action_resolver.resolve_action(actoids[-1], test_battle_master_fighter_lvl_3)
        actoids.append(get_action(test_battle_master_fighter_lvl_3))
        action_resolver.resolve_action(actoids[-1], test_battle_master_fighter_lvl_3)
        actoids.append(get_action(test_battle_master_fighter_lvl_3))
        action_resolver.resolve_action(actoids[-1], test_battle_master_fighter_lvl_3)
    except Exception as e:
        assert False, f"Raised an exception {e}"
    assert str(actoids[0]).startswith('(')
    assert str(actoids[1]) == 'Menacing Greatsword on Fighter 2nd LVL (1)'


def test_error_case_32(battle_map, teams, effect_tracker, test_ghoul, test_skeleton, test_goblin, test_hobgoblin):
    """
    This is trying to reproduce a very serious error which seems to have been introduced together with the NOP action.
    The NOP action if it precedes a regular action will have all accessible coordinates as eligible. The NOP itself will
    be subsequently filtered out and the following action will end up with an incompatible coordinate. So far, the
    feasibility multiplier was masking this issue by making sure those unfeasible choices were not begin selected.

    As a result, the NOP action has been removed again
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_ghoul, test_skeleton, test_goblin, test_hobgoblin]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)

    teams.add_combatant_to_team(test_ghoul, Teams.Color.RED)
    teams.add_combatant_to_team(test_skeleton, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_hobgoblin, Teams.Color.BLUE)

    # I'm trying to create a space where there's no danger zone
    battle_map.set_combatant_coordinates(test_ghoul, np.array([0, 14]))
    battle_map.set_combatant_coordinates(test_skeleton, np.array([4, 14]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([0, 11]))
    battle_map.set_combatant_coordinates(test_hobgoblin, np.array([2, 12]))

    battle_map.build_adjacency_matrix()

    actoids = []
    try:
        actoids.append(get_action(test_ghoul))
        action_resolver.resolve_action(actoids[-1], test_ghoul)
        actoids.append(get_action(test_ghoul))
        action_resolver.resolve_action(actoids[-1], test_ghoul)
        actoids.append(get_action(test_ghoul))
        action_resolver.resolve_action(actoids[-1], test_ghoul)
        assert any(str(act).startswith("Claws on") for act in actoids)
        assert any(str(act).startswith("(") for act in actoids)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_error_case_33(battle_map, teams, effect_tracker, test_battle_master_fighter_lvl_3, test_assassin_rogue_3lvl, test_orc):
    """
    This test case is based on an error encountered during testing. The rogue was able to activate sneak attack despite
    shooting at disadvantage. Then the rogue took AoOs despite still having cunning disengage available.
    # The rogue uses sneak attack despite rolling with disadvantage and doesn't use disengage
    # Orc (4) is alive with 6 hp
    # Assassin Rogue 3rd LVL (1) is alive with 6 hp
    # Battlemaster Fighter 3rd LVL (1) is alive with 9 hp
    # Orc (3) is alive with 4 hp
    # Orc (2) is alive with 3 hp
    # Orc (1) is dead
    # It's Assassin Rogue 3rd LVL (1)'s turn
    # 00 00	00	00	00	00	00	00	00	00	00	XX	XX	XX	00
    # 00 00	00	00	00	00	00	00	00	00	00	XX	XX	XX	00
    # 00 00	00	00	00	00	00	00	00	00	00	00	00	00	00
    # 00 00	00	00	00	00	00	00	00	00	00	00	00	00	00
    # XX XX	XX	00	00	00	00	00	00	00	00	00	00	00	00
    # XX XX	XX	00	00	00	00	00	00	00	00	00	00	00	00
    # XX XX	XX	00	00	00	00	00	00	00	00	00	00	00	00
    # 00 00	00	00	00	00	00	00	00	00	00	00	00	00	00
    # 00 00	00	00	00	00	00	00	00	00	00	00	00	00	00
    # 00 00	00	00	00	00	00	00	O2	00	00	00	00	00	00
    # 00 00	00	00	00	00	00	B1	00	00	00	00	00	00	00
    # 00 00	00	00	00	00	00	00	00	00	00	00	00	00	00
    # O3 O4	00	00	00	00	00	00	00	00	00	00	00	00	00
    # A1 00	00	00	00	00	00	00	00	00	00	00	00	00	00
    # 00 00	00	00	00	00	00	00	00	00	00	00	00	00	00
    #
    # Assassin Rogue 3rd LVL (1) attacks Orc (2) with Shortbow at disadvantage
    # The attack hits Orc (2) for 9 damage
    # Activating Sneak Attack
    # With extra 5 damage from Sneak Attack
    # Orc (2) died
    # Assassin Rogue 3rd LVL (1) moved to [1 1]
    # Orc (3) took an AoO Greataxe on Assassin Rogue 3rd LVL (1) against Assassin Rogue 3rd LVL (1)
    # Orc (3) attacks Assassin Rogue 3rd LVL (1) with Greataxe
    # The attack misses Assassin Rogue 3rd LVL (1)
    # Assassin Rogue 3rd LVL (1) moved to [2 2]
    # Orc (4) took an AoO Greataxe on Assassin Rogue 3rd LVL (1) against Assassin Rogue 3rd LVL (1)
    # Orc (4) attacks Assassin Rogue 3rd LVL (1) with Greataxe
    # The attack hits Assassin Rogue 3rd LVL (1) for 14 damage
    # Assassin Rogue 3rd LVL (1) died
    """
    CustomLogger(logging.WARNING)
    # Renaming them to match the grid
    test_orc.name = "Orc (3)"
    test_orc2 = copy.deepcopy(test_orc)
    test_orc2.name = "Orc (4)"
    test_orc3 = copy.deepcopy(test_orc)
    test_orc3.name = "Orc (2)"
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_battle_master_fighter_lvl_3, test_assassin_rogue_3lvl, test_orc, test_orc2, test_orc3]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)

    teams.add_combatant_to_team(test_battle_master_fighter_lvl_3, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_assassin_rogue_3lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_orc, Teams.Color.RED)
    teams.add_combatant_to_team(test_orc2, Teams.Color.RED)
    teams.add_combatant_to_team(test_orc3, Teams.Color.RED)

    battle_map.place_circular_element(np.array([1, 9]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([12, 14]), Terrain.IMPASSABLE_TERRAIN, radius=1)

    # I'm trying to create a space where there's no danger zone
    battle_map.set_combatant_coordinates(test_battle_master_fighter_lvl_3, np.array([0, 1]))
    battle_map.set_combatant_coordinates(test_assassin_rogue_3lvl, np.array([7, 4]))
    battle_map.set_combatant_coordinates(test_orc, np.array([0, 2]))
    battle_map.set_combatant_coordinates(test_orc2, np.array([1, 2]))
    battle_map.set_combatant_coordinates(test_orc3, np.array([8, 5]))

    test_orc.curr_hp = 4
    test_orc2.curr_hp = 6
    test_orc3.curr_hp = 3
    test_battle_master_fighter_lvl_3.curr_hp = 9
    for combatant in combatants:
        combatant.curr_init = 0  # To prevent assassinate from crashing
    # Can't seem to replicate the behavior from the error but the rogue probably wanted to get as far away as possible
    # using cunning dash instead of using cunning disengage. This may uncover it better than the actual scenario
    test_assassin_rogue_3lvl.has_action = False

    battle_map.build_adjacency_matrix()

    actoids = []
    try:
        actoids.append(get_action(test_assassin_rogue_3lvl))
        action_resolver.resolve_action(actoids[-1], test_assassin_rogue_3lvl)
        actoids.append(get_action(test_assassin_rogue_3lvl))
        action_resolver.resolve_action(actoids[-1], test_assassin_rogue_3lvl)
        actoids.append(get_action(test_assassin_rogue_3lvl))
        action_resolver.resolve_action(actoids[-1], test_assassin_rogue_3lvl)
        actoids.append(get_action(test_assassin_rogue_3lvl))
        action_resolver.resolve_action(actoids[-1], test_assassin_rogue_3lvl)
        actoids.append(get_action(test_assassin_rogue_3lvl))
        action_resolver.resolve_action(actoids[-1], test_assassin_rogue_3lvl)
        assert str(actoids[0]).startswith("Cunning Disengage")
    except Exception as e:
        assert False, f"Raised an exception {e}"


# ----------------------------------
# Young Red Dragon (1) is alive with 140 hp
# Moon Druid 5th LVL (1) wildshaped into Giant Toad is alive with 39 hp
# Draconic Sorcerer 5th LVL (1) is alive with 37 hp
# Battlemaster Fighter 5th LVL (1) is alive with 46 hp
# Totem Barbarian 5th LVL (1) is alive with 61 hp
# 00	00	00	00	00	00	00	00	00	00	00	00	00	00	00
# 00	00	00	00	00	00	00	00	00	00	00	00	00	00	00
# 00	00	00	XX	00	00	00	00	00	00	00	00	00	D1	00
# 00	00	XX	00	00	00	00	00	00	Ma	Ma	00	00	00	00
# 00	00	00	00	00	00	00	00	00	Ma	Ma	T1	00	00	00
# 00	00	00	00	00	00	00	00	00	00	00	Y1	Y1	00	00
# 00	00	00	00	00	00	00	00	00	00	B1	Y1	Y1	00	00
# 00	00	00	00	00	00	00	00	00	00	00	00	00	00	00
# 00	00	00	00	00	00	00	00	00	00	00	00	00	00	00
# 00	00	XX	00	00	00	00	00	00	00	00	00	00	00	00
# 00	00	00	00	00	00	00	00	00	00	00	00	00	00	00
# 00	00	00	00	00	00	00	XX	00	00	00	00	00	00	00
# 00	00	00	00	00	00	00	00	00	00	00	00	00	00	00
# 00	00	00	00	00	00	00	00	00	00	00	00	00	00	00
# 00	00	00	00	00	00	00	00	00	00	00	00	00	00	00
#
# Round 3:
# It's Young Red Dragon (1)'s turn
# 00	00	00	00	00	00	00	00	00	00	00	00	00	00	00
# 00	00	00	00	00	00	00	00	00	00	00	00	00	00	00
# 00	00	00	XX	00	00	00	00	00	00	00	00	00	D1	00
# 00	00	XX	00	00	00	00	00	00	Ma	Ma	00	00	00	00
# 00	00	00	00	00	00	00	00	00	Ma	Ma	T1	00	00	00
# 00	00	00	00	00	00	00	00	00	00	00	Y1	Y1	00	00
# 00	00	00	00	00	00	00	00	00	00	B1	Y1	Y1	00	00
# 00	00	00	00	00	00	00	00	00	00	00	00	00	00	00
# 00	00	00	00	00	00	00	00	00	00	00	00	00	00	00
# 00	00	XX	00	00	00	00	00	00	00	00	00	00	00	00
# 00	00	00	00	00	00	00	00	00	00	00	00	00	00	00
# 00	00	00	00	00	00	00	XX	00	00	00	00	00	00	00
# 00	00	00	00	00	00	00	00	00	00	00	00	00	00	00
# 00	00	00	00	00	00	00	00	00	00	00	00	00	00	00
# 00	00	00	00	00	00	00	00	00	00	00	00	00	00	00
#
# Young Red Dragon (1)'s dodge fades
# Totem Barbarian 5th LVL (1) taken an AoO Two-handed axe on Young Red Dragon (1) against Young Red Dragon (1)
# Totem Barbarian 5th LVL (1) attacks Young Red Dragon (1) with Two-handed axe
# The attack misses Young Red Dragon (1)
# Moon Druid 5th LVL (1) wildshaped into Giant Toad took an AoO Toad Bite on Young Red Dragon (1) against Young Red Dragon (1)
# Moon Druid 5th LVL (1) wildshaped into Giant Toad attacks Young Red Dragon (1) with Bite
# The attack misses Young Red Dragon (1)
# Young Red Dragon (1) moved to [11  7]
# Young Red Dragon (1) moved to [10  6]
# Young Red Dragon (1) moved to [9 6]
# Young Red Dragon (1) moved to [8 6]
# Battlemaster Fighter 5th LVL (1) taken an AoO Greatsword on Young Red Dragon (1) against Young Red Dragon (1)
# Battlemaster Fighter 5th LVL (1) attacks Young Red Dragon (1) with Greatsword
# The attack hits Young Red Dragon (1) for 12 damage
# Young Red Dragon (1) moved to [7 6]
# Young Red Dragon (1) moved to [7 7]
# Young Red Dragon (1) moved to [6 6]
# Young Red Dragon (1) moved to [6 5]
# Young Red Dragon (1) moved to [7 6]
# Young Red Dragon (1) moved to [7 7]
# Young Red Dragon (1) moved to [6 6]
# Young Red Dragon (1) moved to [6 5]
# Young Red Dragon (1) moved to [7 6]
# Young Red Dragon (1) moved to [7 7]
# Young Red Dragon (1) moved to [6 6]
# Young Red Dragon (1) moved to [6 5]
# Action Fire Breath from (7, 7) at 53.5 deg by Young Red Dragon (1) is not feasible. Taking the Dodge action!
