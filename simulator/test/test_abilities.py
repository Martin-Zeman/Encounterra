import copy

import numpy as np
import pytest

from simulator.abilities.wildshape import WildshapeFactory
from simulator.action_resolver import ActionResolver, ActionResult
from simulator.actions.action_selector import get_action
from simulator.actions.action_types import BonusAction
from simulator.battle_map import Terrain
from simulator.combatants.dire_wolf import DireWolf
from simulator.combatants.giant_constrictor_snake import GiantConstrictorSnake
from simulator.logging.custom_logger import CustomLogger, LogLevel
from simulator.misc import DamageType, Conditions
from simulator.teams import Teams
from simulator.test.fixtures import test_moon_druid, test_bugbear, test_giant_toad, teams, effect_tracker, battle_map
from simulator.utils.utils import preallocate_wildshape_forms

from simulator.test.test_singleton import SingletonClass


def test_basic_wildshape(battle_map, teams, effect_tracker, test_moon_druid, test_bugbear):
    """
    We assert the basic functionality of the wildshape ability. The Druid must be able to wildshape and attack.
    """
    CustomLogger(LogLevel.WARNING)

    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_moon_druid, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([0, 0]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 4]))  # Have to set it for fireball placement
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_moon_druid, test_bugbear]
    test_moon_druid.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid, BonusAction.MOON_WILDSHAPE, test_moon_druid.wildshape_factory[1])
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    test_moon_druid.concentration_effect = "FooBar"  # Must be non-None, This way we exclude all the concentration spells from the selection

    try:
        actoid1 = get_action(test_moon_druid)
        assert str(actoid1) == "Wildshape of MoonDruid5Lvl into GiantToad"
        action_resolver.resolve_action(actoid1, test_moon_druid)
        actoid2 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid2, test_moon_druid)
        actoid3 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid3, test_moon_druid)
        actoid4 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid4, test_moon_druid)
        actoid5 = get_action(test_moon_druid)
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
    teams.add_combatant_to_team(test_moon_druid, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([0, 0]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 4]))  # Have to set it for fireball placement
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_moon_druid, test_bugbear]
    test_moon_druid.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid, BonusAction.MOON_WILDSHAPE, test_moon_druid.wildshape_factory[1])
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    test_bugbear.curr_hp = 1000  # Give the target a bunch of HP to make sure it doesn't die

    try:
        actoid1 = get_action(test_moon_druid)
        assert str(actoid1).startswith("Flaming Sphere")
        action_resolver.resolve_action(actoid1, test_moon_druid)
        actoid2 = get_action(test_moon_druid)
        assert str(actoid2) == "Wildshape of MoonDruid5Lvl into GiantToad"
        action_resolver.resolve_action(actoid2, test_moon_druid)
        actoid3 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid3, test_moon_druid)
        assert str(actoid3) == "[1 1]"
        actoid4 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid4, test_moon_druid)
        assert str(actoid4) == "[1 1]"
        test_moon_druid.new_turn()
        actoid5 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid5, test_moon_druid)
        actoid6 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid6, test_moon_druid)
        actoid7 = get_action(test_moon_druid)
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
    teams.add_combatant_to_team(test_moon_druid, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([1, 0]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(test_bugbear, np.array([7, 6]))  # Have to set it for fireball placement
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_moon_druid, test_bugbear]
    test_moon_druid.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid, BonusAction.MOON_WILDSHAPE, test_moon_druid.wildshape_factory[1])
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    test_bugbear.curr_hp = 1000  # Give the target a bunch of HP to make sure it doesn't die

    try:
        actoid1 = get_action(test_moon_druid)
        assert str(actoid1) =="[0 1]"
        action_resolver.resolve_action(actoid1, test_moon_druid)
        actoid2 = get_action(test_moon_druid)
        assert str(actoid2) == "[0 1]"
        action_resolver.resolve_action(actoid2, test_moon_druid)
        actoid3 = get_action(test_moon_druid)
        assert str(actoid3) == "[1 1]"
        action_resolver.resolve_action(actoid3, test_moon_druid)
        actoid4 = get_action(test_moon_druid)
        assert str(actoid4) == "[1 0]"
        action_resolver.resolve_action(actoid4, test_moon_druid)
        actoid5 = get_action(test_moon_druid)
        assert str(actoid5) == "[1 1]" or str(actoid5) == "[1 0]" or str(actoid5) == '[ 1 -1]'
        action_resolver.resolve_action(actoid5, test_moon_druid)

        actoid7 = get_action(test_moon_druid)
        assert str(actoid7).startswith("Flaming Sphere")
        action_resolver.resolve_action(actoid7, test_moon_druid)
        actoid8 = get_action(test_moon_druid)
        assert str(actoid8) == "Wildshape of MoonDruid5Lvl into GiantToad"
        action_resolver.resolve_action(actoid8, test_moon_druid)
        actoid9 = get_action(test_moon_druid)
        assert str(actoid9) == "None"
        test_moon_druid.new_turn()

        actoid10 = get_action(test_moon_druid)
        print()
        print(str(actoid7))
        print("actoid10 " + str(actoid10))
        action_resolver.resolve_action(actoid10, test_moon_druid)
        actoid11 = get_action(test_moon_druid)
        print("actoid11 " + str(actoid11))
        action_resolver.resolve_action(actoid11, test_moon_druid)
        actoid12 = get_action(test_moon_druid)
        print("actoid12 " + str(actoid12))
        action_resolver.resolve_action(actoid12, test_moon_druid)
        actoid13 = get_action(test_moon_druid)
        print("actoid13 " + str(actoid13))
        action_resolver.resolve_action(actoid13, test_moon_druid)
        actoid14 = get_action(test_moon_druid)
        print("actoid14 " + str(actoid14))
        action_resolver.resolve_action(actoid14, test_moon_druid)
        actoid15 = get_action(test_moon_druid)
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
    teams.add_combatant_to_team(test_moon_druid, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([0, 0]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 4]))  # Have to set it for fireball placement
    battle_map.build_adjacency_matrix()
    combatants = [test_moon_druid, test_bugbear]
    test_moon_druid.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid, BonusAction.MOON_WILDSHAPE, test_moon_druid.wildshape_factory[1])
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    class DummyEffect:
        def deactivate(self):
            test_moon_druid.break_concentration()

        def is_affecting(self, combatant):
            return False
    dummy_effect = DummyEffect()
    test_moon_druid.concentration_effect = dummy_effect  # Must be non-None, This way we exclude all the concentration spells from the selection
    battle_map.effect_tracker.add(dummy_effect)

    try:
        actoid1 = get_action(test_moon_druid)
        assert test_moon_druid.curr_hp == 42
        assert str(actoid1) == "Wildshape of MoonDruid5Lvl into GiantToad"
        action_resolver.resolve_action(actoid1, test_moon_druid)
        assert test_moon_druid.get_current_form() is not test_moon_druid
        assert test_moon_druid.current_wildshape_form is not None
        assert test_moon_druid.get_current_form().curr_hp == 39
        test_moon_druid.get_current_form().receive_dmg(40, DamageType.Slashing)
        if not test_moon_druid.concentration_effect:  # The damage could have interrupted it
            test_moon_druid.concentration_effect = dummy_effect  # Must be non-None, This way we exclude all the concentration spells from the selection
            battle_map.effect_tracker.add(dummy_effect)
        assert test_moon_druid.get_current_form() is test_moon_druid
        assert test_moon_druid.current_wildshape_form is None
        assert test_moon_druid.curr_hp == 41
        test_moon_druid.new_turn()
        actoid2 = get_action(test_moon_druid)
        assert str(actoid2) == "Wildshape of MoonDruid5Lvl into GiantToad"
        action_resolver.resolve_action(actoid2, test_moon_druid)
        assert test_moon_druid.get_current_form() is not test_moon_druid
        assert test_moon_druid.current_wildshape_form is not None
        assert test_moon_druid.get_current_form().curr_hp == 39
        test_moon_druid.get_current_form().receive_dmg(42, DamageType.Slashing)
        assert test_moon_druid.get_current_form() is test_moon_druid
        assert test_moon_druid.current_wildshape_form is None
        assert test_moon_druid.curr_hp == 38
        actoid3 = get_action(test_moon_druid)
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
    teams.add_combatant_to_team(test_moon_druid, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([0, 0]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 4]))  # Have to set it for fireball placement
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_moon_druid, test_bugbear]
    test_moon_druid.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid, BonusAction.MOON_WILDSHAPE, test_moon_druid.wildshape_factory[1])
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    class DummyEffect:
        def deactivate(self):
            pass
    dummy_effect = DummyEffect()
    test_moon_druid.concentration_effect = dummy_effect  # Must be non-None, This way we exclude all the concentration spells from the selection

    try:
        actoid1 = get_action(test_moon_druid)
        assert str(actoid1) == "Wildshape of MoonDruid5Lvl into GiantToad"
        action_resolver.resolve_action(actoid1, test_moon_druid)
        actoid2 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid2, test_moon_druid)
        actoid3 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid3, test_moon_druid)
        actoid4 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid4, test_moon_druid)

        actoid5 = get_action(test_bugbear)
        assert str(actoid5) == "Morningstar on MoonDruid5Lvl wildshaped into GiantToad"
        action_resolver.resolve_action(actoid5, test_bugbear)
    except Exception as e:
        assert False, f"Raised an exception {e}"



def test_wilshape_get_eligible_coords(battle_map, teams, effect_tracker, test_moon_druid, test_bugbear):
    """
    We make sure there's a clearing in the terrain which the giant form fits into. It starts at root coordinate [9, 8].
    """
    battle_map.set_effect_tracker(effect_tracker)
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
    test_moon_druid.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid, BonusAction.MOON_WILDSHAPE,
                                                                            test_moon_druid.wildshape_factory[1])

    wsf = WildshapeFactory(test_moon_druid, BonusAction.MOON_WILDSHAPE)
    ws = wsf.create(GiantConstrictorSnake)
    coords = ws.get_eligible_coords(distances, shortest_paths)
    assert coords == [(9, 9)]

def test_wilshape_copy_two_druids(battle_map, teams, effect_tracker, test_moon_druid, test_bugbear):
    """
    We make sure there's a clearing in the terrain which the giant form fits into. It starts at root coordinate [9, 8].
    """
    test_moon_druid_2 = copy.deepcopy(test_moon_druid)
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_moon_druid, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([0, 0]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 4]))  # Have to set it for fireball placement
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_moon_druid, test_bugbear]
    test_moon_druid.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid, BonusAction.MOON_WILDSHAPE, test_moon_druid.wildshape_factory[1])
    test_moon_druid_2.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid_2, BonusAction.MOON_WILDSHAPE, test_moon_druid_2.wildshape_factory[1])
    assert test_moon_druid.available_wildshape_forms[0] is not test_moon_druid_2.available_wildshape_forms[0]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)


def test_bite_and_swallow(battle_map, teams, effect_tracker, test_giant_toad, test_bugbear):
    """
    We assert the basic functionality of the wildshape ability. The Druid must be able to wildshape and attack.
    """
    CustomLogger(LogLevel.WARNING)

    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_giant_toad, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_giant_toad, np.array([2, 2]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 4]))  # Have to set it for fireball placement
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_giant_toad, test_bugbear]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    test_bugbear.ac = 0  # Making sure the attacks hit, only nat 1 can make the test fail
    test_bugbear.curr_hp = 100  # Making sure it doesn't die in case of a crit

    try:
        actoid1 = get_action(test_giant_toad)
        assert str(actoid1) == "Bite on Bugbear"
        result = action_resolver.resolve_action(actoid1, test_giant_toad)
        if result is ActionResult.DMG:
            assert test_bugbear.is_affected_by(Conditions.GRAPPLED)
            assert test_bugbear.is_affected_by(Conditions.RESTRAINED)
            assert test_giant_toad.constricted_target is test_bugbear
            actoid2 = get_action(test_giant_toad)
            assert str(actoid2) == "None"
            test_giant_toad.new_turn()
            actoid3 = get_action(test_giant_toad)
            assert str(actoid3) == "Bite and Swallow on Bugbear"
            swallowed = action_resolver.resolve_action(actoid3, test_giant_toad)
            if swallowed is ActionResult.DMG:
                assert test_giant_toad.constricted_target is None
                assert test_giant_toad.swallowed_target is test_bugbear
                assert test_bugbear.is_affected_by(Conditions.RESTRAINED)
                assert test_bugbear.is_affected_by(Conditions.BLINDED)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_cannot_wildshape_restrained_in_confined_space(battle_map, teams, effect_tracker, test_giant_toad, test_moon_druid):
    """
    We assert that the druid doesn't plan a wildshape action when grappled and unable to move to a place where there's the space to do so.
    """
    CustomLogger(LogLevel.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_moon_druid, test_giant_toad]
    test_moon_druid.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid, BonusAction.MOON_WILDSHAPE, test_moon_druid.wildshape_factory[1])
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_giant_toad, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_moon_druid, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([1, 14]))
    battle_map.set_combatant_coordinates(test_giant_toad, np.array([0, 12]))
    battle_map.build_adjacency_matrix()
    test_moon_druid.ac = 0  # Make sure the bite hits (expect for nat 1)
    for af in test_giant_toad.action_factories:
        try:
            af[1].to_hit = 100
        except AttributeError:
            pass
    test_moon_druid.athletics = -20  # Make sure it can't break the grapple
    test_moon_druid.acrobatics = -20  # Make sure it can't break the grapple

    try:
        actoid1 = get_action(test_giant_toad)
        action_resolver.resolve_action(actoid1, test_giant_toad)
        if test_moon_druid.is_affected_by(Conditions.GRAPPLED):
            actoid2 = get_action(test_moon_druid)
            action_resolver.resolve_action(actoid2, test_moon_druid)
            if test_moon_druid.is_affected_by(Conditions.GRAPPLED):  # Still grappled
                actoid3 = get_action(test_moon_druid)
                assert str(actoid3) == "None"
    except Exception as e:
        assert False, f"Raised an exception {e}"

@pytest.fixture(autouse=True)
def reset_singleton():
    SingletonClass._instance = None

def test_singleton_1():
    obj1 = SingletonClass(10)
    assert obj1.number == 10

def test_singleton_2():
    obj1 = SingletonClass(20)
    assert obj1.number == 20
