import cProfile
import copy
import logging
import pstats

import numpy as np
import pytest

from ..abilities.lay_on_hands import LayOnHandsFactory
from ..abilities.wildshape import WildshapeFactory
from ..action_resolver import ActionResolver, ActionResult
from ..actions.action_selector import get_action
from ..actions.action_types import BonusAction, Action
from ..actions.hide import HideFactory
from ..battle_map import Terrain
from ..combatants.giant_constrictor_snake import GiantConstrictorSnake
from ..effects.effect import EffectType
from ..logging.custom_logger import CustomLogger
from ..misc import DamageType, SavingThrow
from ..conditions import Conditions, is_affected_by
from ..resources import ResourceDepletionLevel
from ..spells.ray_of_enfeeblement import RayOfEnfeeblementFactory
from ..spells.sleep import SleepFactory
from ..teams import Teams
from ..test.fixtures import test_moon_druid, test_bugbear, test_giant_toad, teams, effect_tracker, battle_map, test_assassin_rogue,\
    test_ogre, test_goblin, test_brown_bear, test_dire_wolf, test_stone_giant, test_totem_barbarian, test_night_hag,\
    test_druid_lvl_1, test_fighter_lvl_1, test_battle_master_fighter_lvl_3, test_paladin_lvl_1, \
    test_young_green_dragon, test_skeleton, test_hobgoblin, test_green_dragon_wyrmling
from ..utils.utils import preallocate_wildshape_forms

from ..test.test_singleton import SingletonClass


def test_basic_wildshape(battle_map, teams, effect_tracker, test_moon_druid, test_bugbear):
    """
    We assert the basic functionality of the wildshape ability. The Druid must be able to wildshape and attack.
    """
    CustomLogger(logging.WARNING)

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
        assert str(actoid1) == "Wildshape of Moon Druid 5th LVL (1) into Giant Toad"
        action_resolver.resolve_action(actoid1, test_moon_druid)
        actoid2 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid2, test_moon_druid)
        actoid3 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid3, test_moon_druid)
        actoid4 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid4, test_moon_druid)
        actoid5 = get_action(test_moon_druid)
        actoid6 = None
        if actoid5:
            action_resolver.resolve_action(actoid5, test_moon_druid)
            actoid6 = get_action(test_moon_druid)
        # It can attack at any of those moments but latest at actoid6
        assert str(actoid4) == "Toad Bite on Bugbear (1)" or str(actoid5) == "Toad Bite on Bugbear (1)" or str(actoid6) == "Toad Bite on Bugbear (1)"
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_wildshape_with_concentration_spell(battle_map, teams, effect_tracker, test_moon_druid, test_goblin):
    """
    We assert the basic functionality of the wildshape ability. The Druid must be able to wildshape and attack.
    """
    CustomLogger(logging.WARNING)

    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_moon_druid, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([0, 0]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(test_goblin, np.array([4, 4]))  # Have to set it for fireball placement
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_moon_druid, test_goblin]
    test_moon_druid.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid, BonusAction.MOON_WILDSHAPE, test_moon_druid.wildshape_factory[1])
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    test_goblin.curr_hp = 1000  # Give the target a bunch of HP to make sure it doesn't die

    try:
        actoid1 = get_action(test_moon_druid)
        assert str(actoid1).startswith("Flaming Sphere")  # We've selected a goblin to make Flaming Sphere to win out over Hold Person
        action_resolver.resolve_action(actoid1, test_moon_druid)
        actoid2 = get_action(test_moon_druid)
        assert str(actoid2) == "Wildshape of Moon Druid 5th LVL (1) into Giant Toad"
        action_resolver.resolve_action(actoid2, test_moon_druid)
        actoid3 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid3, test_moon_druid)
        # assert str(actoid3) == "[1 1]"
        actoid4 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid4, test_moon_druid)
        # assert str(actoid4) == "[1 1]"
        test_moon_druid.new_turn()
        actoid5 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid5, test_moon_druid)
        actoid6 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid6, test_moon_druid)
        actoid7 = get_action(test_moon_druid)
        assert str(actoid5) == "Toad Bite on Goblin (1)" or str(actoid6) == "Toad Bite on Goblin (1)"
        assert str(actoid5) == "Flaming Sphere Ram into Goblin (1)" or str(actoid6) == "Flaming Sphere Ram into Goblin (1)"
        assert str(actoid7) == "None"
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_movement_before_wildshape_with_concentration_spell(battle_map, teams, effect_tracker, test_moon_druid, test_bugbear):
    """
    We assert that action plan combination works with a concentration spell even when the druid first has to move in order to wildshape.
    There's a sort of a tunnel the druid first needs to get out of.
    """
    CustomLogger(logging.WARNING)

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
        assert str(actoid1) == "(0, 1)"
        action_resolver.resolve_action(actoid1, test_moon_druid)
        actoid2 = get_action(test_moon_druid)
        assert str(actoid2) == "(0, 1)"
        action_resolver.resolve_action(actoid2, test_moon_druid)
        actoid3 = get_action(test_moon_druid)
        assert str(actoid3) == "(1, 1)"
        action_resolver.resolve_action(actoid3, test_moon_druid)
        actoid4 = get_action(test_moon_druid)
        assert str(actoid4) == "(1, 0)"
        action_resolver.resolve_action(actoid4, test_moon_druid)
        actoid5 = get_action(test_moon_druid)
        assert str(actoid5) == "(1, 1)" or str(actoid5) == "(1, 0)" or str(actoid5) == '(1, -1)'
        action_resolver.resolve_action(actoid5, test_moon_druid)

        actoid7 = get_action(test_moon_druid)
        assert actoid7.factory.concentration
        action_resolver.resolve_action(actoid7, test_moon_druid)
        actoid8 = get_action(test_moon_druid)
        assert str(actoid8) == "Wildshape of Moon Druid 5th LVL (1) into Giant Toad"
        action_resolver.resolve_action(actoid8, test_moon_druid)
        actoid9 = get_action(test_moon_druid)
        assert str(actoid9) == "None"
        test_moon_druid.new_turn()

        actoid10 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid10, test_moon_druid)
        actoid11 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid11, test_moon_druid)
        actoid12 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid12, test_moon_druid)
        actoid13 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid13, test_moon_druid)
        actoid14 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid14, test_moon_druid)
        actoid15 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid15, test_moon_druid)
        second_turn_actoids = [str(actoid10), str(actoid11), str(actoid12), str(actoid13), str(actoid14), str(actoid15)]
        assert any(act == "Toad Bite on Bugbear (1)" for act in second_turn_actoids)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_damage_knocks_out_of_wildshape(battle_map, teams, effect_tracker, test_moon_druid, test_bugbear):
    """
    We assert that damage can knock the druid out of the wildshape and that damage carries over to the original form.
    We also assert that the druid will attempt to wildshape again after being knocked out the first time. Also that the druid
    cannot wildshape a third time. We also test that the bugbear is really swallowed.
    """
    CustomLogger(logging.WARNING)

    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_moon_druid, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([2, 2]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 4]))
    battle_map.build_adjacency_matrix()
    combatants = [test_moon_druid, test_bugbear]
    test_moon_druid.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid, BonusAction.MOON_WILDSHAPE, test_moon_druid.wildshape_factory[1])
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    class DummyFactory:
        def __init__(self):
            self.combatant = None
    class DummyEffect:
        def __init__(self):
            self.factory = DummyFactory()
            self.initiator = test_moon_druid
        def deactivate(self):
            test_moon_druid.break_concentration()

        def deactivate_for_combatant(self, combatant):
            assert False

        def is_affecting(self, combatant):
            return False

        def get_effect_type(self):
            return EffectType.FAERIE_FIRE
    dummy_effect = DummyEffect()
    test_moon_druid.concentration_effect = dummy_effect  # Must be non-None, This way we exclude all the concentration spells from the selection
    battle_map.effect_tracker.add(dummy_effect)
    test_bugbear.curr_hp = 100  # Making sure it survives

    try:
        actoid1 = get_action(test_moon_druid)
        assert test_moon_druid.curr_hp == 43
        assert str(actoid1).startswith("Thunderwave")
        action_resolver.resolve_action(actoid1, test_moon_druid)
        battle_map.move_combatant(test_bugbear, np.array([4, 4]))  # Move him back in case he got pushed away
        actoid2 = get_action(test_moon_druid)
        assert test_moon_druid.curr_hp == 43
        assert str(actoid2) == "Wildshape of Moon Druid 5th LVL (1) into Giant Toad"
        action_resolver.resolve_action(actoid2, test_moon_druid)
        assert test_moon_druid.get_current_form() is not test_moon_druid
        assert test_moon_druid.current_wildshape_form is not None
        assert test_moon_druid.get_current_form().curr_hp == 39

        test_bugbear.ac = 0  # Making sure the toad hits

        test_moon_druid.new_turn()
        actoid3 = get_action(test_moon_druid)
        assert str(actoid3) == "Toad Bite on Bugbear (1)"
        action_resolver.resolve_action(actoid3, test_moon_druid)
        test_moon_druid.new_turn()
        actoid4 = get_action(test_moon_druid)
        assert str(actoid4) == "Toad Bite and Swallow on Bugbear (1)"
        action_resolver.resolve_action(actoid4, test_moon_druid)
        assert is_affected_by(test_bugbear, Conditions.SWALLOWED)
        test_moon_druid.get_current_form().receive_dmg(40, DamageType.Slashing)
        assert not is_affected_by(test_bugbear, Conditions.SWALLOWED)
        assert test_bugbear.is_swallowed == [False, None]
        if not test_moon_druid.concentration_effect:  # The damage could have interrupted it
            test_moon_druid.concentration_effect = dummy_effect  # Must be non-None, This way we exclude all the concentration spells from the selection
            battle_map.effect_tracker.add(dummy_effect)
        assert test_moon_druid.get_current_form() is test_moon_druid
        assert test_moon_druid.current_wildshape_form is None
        assert test_moon_druid.curr_hp == 42
        test_moon_druid.new_turn()
        actoid5 = get_action(test_moon_druid)
        assert str(actoid5) == "Wildshape of Moon Druid 5th LVL (1) into Brown Bear"
        action_resolver.resolve_action(actoid5, test_moon_druid)
        assert test_moon_druid.get_current_form() is not test_moon_druid
        assert test_moon_druid.current_wildshape_form is not None
        assert test_moon_druid.get_current_form().curr_hp == 34
        test_moon_druid.get_current_form().receive_dmg(42, DamageType.Slashing)
        assert test_moon_druid.get_current_form() is test_moon_druid
        assert test_moon_druid.current_wildshape_form is None
        assert test_moon_druid.curr_hp == 34
        actoid6 = get_action(test_moon_druid)
        assert not str(actoid6).startswith("Wildshape")
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_removed_from_battlemap_when_killed_by_carry_over_damage_in_wildshape(battle_map, teams, effect_tracker, test_moon_druid, test_bugbear):
    """
    We assert that the carry-over damage from wildshape will remove the druid from the map when killed by it.
    """
    CustomLogger(logging.WARNING)

    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_moon_druid, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([2, 2]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 4]))
    battle_map.build_adjacency_matrix()
    combatants = [test_moon_druid, test_bugbear]
    test_moon_druid.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid, BonusAction.MOON_WILDSHAPE, test_moon_druid.wildshape_factory[1])
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    class DummyFactory:
        def __init__(self):
            self.combatant = None
    class DummyEffect:
        def __init__(self):
            self.factory = DummyFactory()
            self.initiator = test_moon_druid
        def deactivate(self):
            test_moon_druid.break_concentration()

        def deactivate_for_combatant(self, combatant):
            assert False

        def is_affecting(self, combatant):
            return False

        def get_effect_type(self):
            return EffectType.FAERIE_FIRE
    dummy_effect = DummyEffect()
    test_moon_druid.concentration_effect = dummy_effect  # Must be non-None, This way we exclude all the concentration spells from the selection
    battle_map.effect_tracker.add(dummy_effect)
    test_moon_druid.curr_hp = 1
    test_moon_druid.spellslots.deplete_resource(ResourceDepletionLevel.FULLY_DEPLETED)  # To prevent the druid from casting Thunderwave or something first

    try:
        actoid1 = get_action(test_moon_druid)
        assert test_moon_druid.curr_hp == 1
        assert str(actoid1) == "Wildshape of Moon Druid 5th LVL (1) into Giant Toad"
        action_resolver.resolve_action(actoid1, test_moon_druid)
        assert test_moon_druid.get_current_form() is not test_moon_druid
        assert test_moon_druid.current_wildshape_form is not None
        assert test_moon_druid.get_current_form().curr_hp == 39
        wildshaped_moon_druid = test_moon_druid.get_current_form()
        wildshaped_moon_druid.receive_dmg(40, DamageType.Slashing)
        battle_map.remove_combatant_if_dead(wildshaped_moon_druid)
        assert not wildshaped_moon_druid.is_alive()
        assert not test_moon_druid.is_alive()
        assert test_moon_druid.get_current_form() is test_moon_druid
        assert test_moon_druid not in battle_map.combatant_coordinate_cache.keys()
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_others_can_attack_wildshape(battle_map, teams, effect_tracker, test_moon_druid, test_bugbear):
    """
    We assert that others can attack a wildshaped druid
    once.
    """
    CustomLogger(logging.WARNING)

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
    test_bugbear.curr_hp = 100 # Making sure it survives the attacks
    class DummyEffect:
        def __init__(self):
            self.initiator = None
        def deactivate(self):
            test_moon_druid.break_concentration()

        def deactivate_for_combatant(self, combatant):
            assert False

        def is_affecting(self, combatant):
            return False

        def get_effect_type(self):
            return None

    dummy_effect = DummyEffect()
    effect_tracker.add(dummy_effect)
    test_moon_druid.concentration_effect = dummy_effect  # Must be non-None, This way we exclude all the concentration spells from the selection

    try:
        actoid1 = get_action(test_moon_druid)
        assert str(actoid1) == "Wildshape of Moon Druid 5th LVL (1) into Giant Toad"
        action_resolver.resolve_action(actoid1, test_moon_druid)
        actoid2 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid2, test_moon_druid)
        actoid3 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid3, test_moon_druid)
        actoid4 = get_action(test_moon_druid)
        action_resolver.resolve_action(actoid4, test_moon_druid)

        actoid5 = get_action(test_bugbear)
        if is_affected_by(test_bugbear, Conditions.GRAPPLED):
            assert str(actoid5) == "Break Grapple"
        else:
            assert str(actoid5) == "Morningstar on Moon Druid 5th LVL (1) wildshaped into Giant Toad"
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


@pytest.mark.flaky(reruns=3)
def test_bite_and_swallow(battle_map, teams, effect_tracker, test_giant_toad, test_bugbear):
    """
    We assert the basic functionality of the wildshape ability. The Druid must be able to wildshape and attack.
    """
    CustomLogger(logging.WARNING)

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
        assert str(actoid1) == "Bite on Bugbear (1)"
        result = action_resolver.resolve_action(actoid1, test_giant_toad)
        if result is ActionResult.DMG:
            assert is_affected_by(test_bugbear, Conditions.GRAPPLED)
            assert is_affected_by(test_bugbear, Conditions.RESTRAINED)
            actoid2 = get_action(test_giant_toad)
            assert str(actoid2) == "None"
            test_giant_toad.new_turn()
            actoid3 = get_action(test_giant_toad)
            assert str(actoid3) == "Bite and Swallow on Bugbear (1)"
            swallowed = action_resolver.resolve_action(actoid3, test_giant_toad)
            if swallowed is ActionResult.DMG:
                assert test_giant_toad.swallowed_target is test_bugbear
                assert is_affected_by(test_bugbear, Conditions.RESTRAINED)
                assert is_affected_by(test_bugbear, Conditions.BLINDED)
                assert is_affected_by(test_bugbear, Conditions.SWALLOWED)
                assert test_giant_toad.swallowed_target is test_bugbear
    except Exception as e:
        assert False, f"Raised an exception {e}"


@pytest.mark.flaky(reruns=3)
def test_cannot_wildshape_restrained_in_confined_space(battle_map, teams, effect_tracker, test_giant_toad, test_moon_druid):
    """
    We assert that the druid doesn't plan a wildshape action when grappled and unable to move to a place where there's the space to do so.
    """
    CustomLogger(logging.WARNING)
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
    test_moon_druid.spellslots.deplete_resource(ResourceDepletionLevel.FULLY_DEPLETED)  # To prevent the druid from casting instead

    try:
        actoid1 = get_action(test_giant_toad)
        action_resolver.resolve_action(actoid1, test_giant_toad)
        if is_affected_by(test_moon_druid, Conditions.GRAPPLED):
            actoid2 = get_action(test_moon_druid)
            action_resolver.resolve_action(actoid2, test_moon_druid)
            if is_affected_by(test_moon_druid, Conditions.GRAPPLED):  # Still grappled
                actoid3 = get_action(test_moon_druid)
                assert str(actoid3) == "None"
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_cunning_hide_geometry(battle_map, teams, effect_tracker, test_assassin_rogue, test_bugbear, test_ogre, test_goblin):
    """
    Based on a scenario encountered during testing. The bounding box overlap test was incorrect.
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    battle_map.place_circular_element(np.array([6, 8]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([8, 2]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([2, 11]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([11, 12]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    teams.add_combatant_to_team(test_assassin_rogue, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    teams.add_combatant_to_team(test_ogre, Teams.Color.RED)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_assassin_rogue, np.array([1, 5]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([12, 8]))
    battle_map.set_combatant_coordinates(test_ogre, np.array([2, 1]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([5, 11]))
    battle_map.build_adjacency_matrix()
    _, shortest_paths = battle_map.calc_dijkstra(test_assassin_rogue)
    battle_map.calc_visibility_dict_for_all_coords(test_assassin_rogue, shortest_paths)

    hf = HideFactory(BonusAction.CUNNING_HIDE, test_assassin_rogue)
    hide = hf.create(test_goblin)
    eligible_coords = hide.get_eligible_coords(None, None)
    assert (5, 10) not in eligible_coords
    assert (6, 10) not in eligible_coords


@pytest.mark.flaky(reruns=3)
def test_cunning_hide_and_sneak_attack(battle_map, teams, effect_tracker, test_assassin_rogue, test_bugbear, test_ogre, test_goblin, test_brown_bear):
    """
    Test scenario where the Rogue has three enemies and no allies (no Sneak Attack via adjacent allies). The Rogue has to find
    a hiding spot, hide, step out of the hiding spot and then attack with Sneak Attack. I had to put the Brown Bear in the bottom right
    corner to prevent the Rogue from running there and make him hide and attack instead.
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    battle_map.place_circular_element(np.array([6, 8]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([8, 2]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([2, 11]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([11, 12]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    combatants = [test_assassin_rogue, test_bugbear, test_ogre, test_goblin, test_brown_bear]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_assassin_rogue, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    teams.add_combatant_to_team(test_ogre, Teams.Color.RED)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    teams.add_combatant_to_team(test_brown_bear, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_assassin_rogue, np.array([1, 5]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([12, 8]))
    battle_map.set_combatant_coordinates(test_ogre, np.array([2, 1]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([5, 11]))
    battle_map.set_combatant_coordinates(test_brown_bear, np.array([13, 0]))
    battle_map.build_adjacency_matrix()
    test_assassin_rogue.stealth = 20  # Making sure the hide always works
    for combatant in combatants:
        combatant.curr_init = 0  # To prevent assassinate from crashing

    try:
        first_turn_actoids = [get_action(test_assassin_rogue)]
        action_resolver.resolve_action(first_turn_actoids[-1], test_assassin_rogue)
        first_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(first_turn_actoids[-1], test_assassin_rogue)
        first_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(first_turn_actoids[-1], test_assassin_rogue)
        first_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(first_turn_actoids[-1], test_assassin_rogue)
        first_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(first_turn_actoids[-1], test_assassin_rogue)
        first_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(first_turn_actoids[-1], test_assassin_rogue)
        first_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(first_turn_actoids[-1], test_assassin_rogue)
        first_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(first_turn_actoids[-1], test_assassin_rogue)
        first_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(first_turn_actoids[-1], test_assassin_rogue)
        first_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(first_turn_actoids[-1], test_assassin_rogue)
        assert any(str(act).startswith("Cunning Hide") for act in first_turn_actoids)
        assert any(str(act).startswith("Shortbow") for act in first_turn_actoids)
        assert next(i for i, act in enumerate(first_turn_actoids) if str(act).startswith("Cunning Hide")) < next(i for i, act in enumerate(first_turn_actoids) if str(act).startswith("Shortbow"))
        assert any(str(act).startswith("(") for act in first_turn_actoids)
        assert list(filter(lambda act: str(act).startswith("Cunning Hide"), first_turn_actoids))[0].target is list(filter(lambda act: str(act).startswith("Shortbow"), first_turn_actoids))[0].target
        test_assassin_rogue.new_turn()
        second_turn_actoids = [get_action(test_assassin_rogue)]
        action_resolver.resolve_action(second_turn_actoids[-1], test_assassin_rogue)
        second_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(second_turn_actoids[-1], test_assassin_rogue)
        second_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(second_turn_actoids[-1], test_assassin_rogue)
        second_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(second_turn_actoids[-1], test_assassin_rogue)
        second_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(second_turn_actoids[-1], test_assassin_rogue)
        second_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(second_turn_actoids[-1], test_assassin_rogue)
        second_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(second_turn_actoids[-1], test_assassin_rogue)
        second_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(second_turn_actoids[-1], test_assassin_rogue)
        assert any(str(act).startswith("Cunning Hide") for act in second_turn_actoids)
        assert any(str(act).startswith("Shortbow") for act in second_turn_actoids)
        assert next(i for i, act in enumerate(second_turn_actoids) if str(act).startswith("Cunning Hide")) < next(i for i, act in enumerate(second_turn_actoids) if str(act).startswith("Shortbow"))
        assert any(str(act).startswith("(") for act in second_turn_actoids)
        assert list(filter(lambda act: str(act).startswith("Cunning Hide"), second_turn_actoids))[0].target is list(filter(lambda act: str(act).startswith("Shortbow"), second_turn_actoids))[0].target
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_cunning_adjacent_enemy_hide_sneak_attack(battle_map, teams, effect_tracker, test_assassin_rogue, test_bugbear, test_ogre, test_goblin):
    """
    Test scenario where the Rogue has two enemies and one ally adjacent to one of the enemies. The Rogue doesn't need to hide to trigger
    Sneak Attack but hiding still gives advantage so the rogue goes for it despite suffering an AoO from the goblin.
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    battle_map.place_circular_element(np.array([6, 8]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([8, 2]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([2, 11]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([11, 12]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    combatants = [test_assassin_rogue, test_bugbear, test_ogre, test_goblin]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_assassin_rogue, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_ogre, Teams.Color.RED)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_assassin_rogue, np.array([1, 5]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 2]))
    battle_map.set_combatant_coordinates(test_ogre, np.array([2, 1]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([5, 11]))
    battle_map.build_adjacency_matrix()
    test_assassin_rogue.stealth = 20  # Making sure the hide always works
    for combatant in combatants:
        combatant.curr_init = 0  # To prevent assassinate from crashing

    try:
        actoid1 = get_action(test_assassin_rogue)
        action_resolver.resolve_action(actoid1, test_assassin_rogue)
        actoid2 = get_action(test_assassin_rogue)
        action_resolver.resolve_action(actoid2, test_assassin_rogue)
        actoid3 = get_action(test_assassin_rogue)
        action_resolver.resolve_action(actoid3, test_assassin_rogue)
        actoid4 = get_action(test_assassin_rogue)
        action_resolver.resolve_action(actoid4, test_assassin_rogue)
        actoid5 = get_action(test_assassin_rogue)
        action_resolver.resolve_action(actoid5, test_assassin_rogue)
        actoid6 = get_action(test_assassin_rogue)
        assert str(actoid6) == "Cunning Hide of Assassin Rogue 5th LVL (1) from Ogre (1)"
        action_resolver.resolve_action(actoid6, test_assassin_rogue)
        actoid7 = get_action(test_assassin_rogue)
        action_resolver.resolve_action(actoid7, test_assassin_rogue)
        actoid8 = get_action(test_assassin_rogue)
        assert str(actoid8) == "Shortbow on Ogre (1)"
        action_resolver.resolve_action(actoid8, test_assassin_rogue)
        actoid9 = get_action(test_assassin_rogue)
        action_resolver.resolve_action(actoid9, test_assassin_rogue)
        actoid10 = get_action(test_assassin_rogue)
        action_resolver.resolve_action(actoid10, test_assassin_rogue)
        test_assassin_rogue.new_turn()
        second_turn_actoids = [get_action(test_assassin_rogue)]
        action_resolver.resolve_action(second_turn_actoids[-1], test_assassin_rogue)
        second_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(second_turn_actoids[-1], test_assassin_rogue)
        second_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(second_turn_actoids[-1], test_assassin_rogue)  # Step of out hiding
        second_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(second_turn_actoids[-1], test_assassin_rogue)
        second_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(second_turn_actoids[-1], test_assassin_rogue)
        second_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(second_turn_actoids[-1], test_assassin_rogue)
        assert any(str(act) == "Cunning Hide of Assassin Rogue 5th LVL (1) from Ogre (1)" for act in second_turn_actoids)
        assert any(str(act) == "Shortbow on Ogre (1)" for act in second_turn_actoids)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_cunning_adjacent_enemy_hide_sneak_attack_2(battle_map, teams, effect_tracker, test_assassin_rogue, test_bugbear, test_ogre, test_goblin):
    """
    Test scenario where the Rogue has two enemies and one ally adjacent to one of the enemies. The Rogue doesn't need to hide to trigger
    Sneak Attack but hiding still gives advantage so the rogue goes for it. Ihis time the hiding spot can be reached in the first turn.
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    battle_map.place_circular_element(np.array([6, 8]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([8, 2]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([2, 9]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([11, 12]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    combatants = [test_assassin_rogue, test_bugbear, test_ogre, test_goblin]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_assassin_rogue, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_ogre, Teams.Color.RED)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_assassin_rogue, np.array([1, 5]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 2]))
    battle_map.set_combatant_coordinates(test_ogre, np.array([2, 1]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([5, 11]))
    battle_map.build_adjacency_matrix()
    test_assassin_rogue.stealth = 20  # Making sure the hide always works
    for combatant in combatants:
        combatant.curr_init = 0  # To prevent assassinate from crashing

    try:
    # from ..actions.action_selector import get_action
    # cProfile.runctx('get_action(test_assassin_rogue)', None, locals(), filename="get_action_stats")
    # p = pstats.Stats("get_action_stats")
    # p.strip_dirs().sort_stats("cumtime").print_stats()
        actoid1 = get_action(test_assassin_rogue)
        action_resolver.resolve_action(actoid1, test_assassin_rogue)
        actoid2 = get_action(test_assassin_rogue)
        action_resolver.resolve_action(actoid2, test_assassin_rogue)
        actoid3 = get_action(test_assassin_rogue)
        action_resolver.resolve_action(actoid3, test_assassin_rogue)
        actoid4 = get_action(test_assassin_rogue)
        action_resolver.resolve_action(actoid4, test_assassin_rogue)
        actoid5 = get_action(test_assassin_rogue)
        action_resolver.resolve_action(actoid5, test_assassin_rogue)
        actoid6 = get_action(test_assassin_rogue)
        # assert str(actoid6).startswith("Cunning Hide of AssassinRogue from Ogre")
        action_resolver.resolve_action(actoid6, test_assassin_rogue)
        actoid7 = get_action(test_assassin_rogue)
        action_resolver.resolve_action(actoid7, test_assassin_rogue)
        actoid8 = get_action(test_assassin_rogue)
        # assert str(actoid8) == "Shortbow on Ogre"
        action_resolver.resolve_action(actoid8, test_assassin_rogue)
        actoids = [actoid1, actoid2, actoid3, actoid4, actoid5, actoid6, actoid7, actoid8]
        # TODO The rogue's not hiding first because there's lone LoS from (2, 10) -> two phase movement?
        test_assassin_rogue.new_turn()
        actoid9 = get_action(test_assassin_rogue)
        action_resolver.resolve_action(actoid9, test_assassin_rogue)
        actoid10 = get_action(test_assassin_rogue)
        action_resolver.resolve_action(actoid10, test_assassin_rogue)
        actoid11 = get_action(test_assassin_rogue)
        action_resolver.resolve_action(actoid11, test_assassin_rogue)  # Step of out hiding
        actoid12 = get_action(test_assassin_rogue)
        action_resolver.resolve_action(actoid12, test_assassin_rogue)
        actoid13 = get_action(test_assassin_rogue)
        action_resolver.resolve_action(actoid12, test_assassin_rogue)
        actoids = [actoid9, actoid10, actoid11, actoid12, actoid13]
        # assert any(str(act) == "Shortbow on Ogre" for act in actoids)
        # assert any(str(act).startswith("Cunning Hide of AssassinRogue from Ogre") for act in actoids)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_cunning_adjacent_enemy_hide_sneak_attack_in_melee(battle_map, teams, effect_tracker, test_stone_giant, test_assassin_rogue, test_dire_wolf):
    """
    Investigation of Rogue's behavior when in the proximity of a Stone Giant. Based on an error case where the Rogue decided to disengage, run
    and dash back instead of hiding and attacking. It asserts that the Rogue does the right thing now.
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_stone_giant, test_assassin_rogue, test_dire_wolf]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    battle_map.place_circular_element(np.array([2, 13]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([11, 10]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([10, 10]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([11, 5]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([5, 5]), Terrain.DIFFICULT_TERRAIN, radius=0)
    teams.add_combatant_to_team(test_stone_giant, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_assassin_rogue, Teams.Color.RED)
    teams.add_combatant_to_team(test_dire_wolf, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_stone_giant, np.array([9, 11]))
    battle_map.set_combatant_coordinates(test_assassin_rogue, np.array([12, 10]))
    battle_map.set_combatant_coordinates(test_dire_wolf, np.array([7, 10]))
    battle_map.build_adjacency_matrix()
    for combatant in combatants:
        combatant.curr_init = 0  # To prevent assassinate from crashing

    try:
        actoid1 = get_action(test_assassin_rogue)
        assert str(actoid1).startswith("(")
        action_resolver.resolve_action(actoid1, test_assassin_rogue)
        actoid2 = get_action(test_assassin_rogue)
        assert str(actoid2) == "Cunning Hide of Assassin Rogue 5th LVL (1) from Stone Giant (1)"
        action_resolver.resolve_action(actoid2, test_assassin_rogue)
        actoid3 = get_action(test_assassin_rogue)
        assert str(actoid3) == "(1, 1)"
        action_resolver.resolve_action(actoid3, test_assassin_rogue)
        actoid4 = get_action(test_assassin_rogue)
        assert str(actoid4).startswith("Rapier")
        action_resolver.resolve_action(actoid4, test_assassin_rogue)
        # actoid5 = get_action(test_assassin_rogue)
        # action_resolver.resolve_action(actoid5, test_assassin_rogue)
        # actoid6 = get_action(test_assassin_rogue)
        # action_resolver.resolve_action(actoid6, test_assassin_rogue)
        # actoid7 = get_action(test_assassin_rogue)
        # action_resolver.resolve_action(actoid7, test_assassin_rogue)
        # actoid8 = get_action(test_assassin_rogue)
        # action_resolver.resolve_action(actoid8, test_assassin_rogue)
        # actoids = [actoid3, actoid4, actoid5, actoid6, actoid7, actoid8]
        # assert any(str(act) == "Rapier on StoneGiant" for act in actoids)
        # assert any(str(act).startswith("(") for act in actoids)
    except Exception as e:
        assert False, f"Raised an exception {e}"


@pytest.mark.flaky(reruns=3)
def test_rogue_cunning_disengage(battle_map, teams, effect_tracker, test_assassin_rogue, test_bugbear, test_ogre, test_goblin):
    """
    Test scenario where the Rogue is surrounded by three enemies. Even though there is a place to hide nearby, the rogue opts to use
    Disengage and Cunning Dash instead. In the second turn the rogue gets into cover, hides, steps out of cover and shoots.
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    battle_map.place_circular_element(np.array([4, 5]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    combatants = [test_assassin_rogue, test_bugbear, test_ogre, test_goblin]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_assassin_rogue, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    teams.add_combatant_to_team(test_ogre, Teams.Color.RED)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_assassin_rogue, np.array([2, 3]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([3, 2]))
    battle_map.set_combatant_coordinates(test_ogre, np.array([1, 1]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([1, 3]))
    battle_map.build_adjacency_matrix()
    test_assassin_rogue.stealth = 20  # Making sure the hide always works
    for combatant in combatants:
        combatant.curr_init = 0  # To prevent assassinate from crashing

    try:
        first_turn_actoids = [get_action(test_assassin_rogue)]
        assert str(first_turn_actoids[-1]) == "Disengage of Assassin Rogue 5th LVL (1)"
        action_resolver.resolve_action(first_turn_actoids[-1], test_assassin_rogue)
        first_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(first_turn_actoids[-1], test_assassin_rogue)
        first_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(first_turn_actoids[-1], test_assassin_rogue)
        first_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(first_turn_actoids[-1], test_assassin_rogue)
        first_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(first_turn_actoids[-1], test_assassin_rogue)
        first_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(first_turn_actoids[-1], test_assassin_rogue)
        first_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(first_turn_actoids[-1], test_assassin_rogue)
        first_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(first_turn_actoids[-1], test_assassin_rogue)
        first_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(first_turn_actoids[-1], test_assassin_rogue)
        first_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(first_turn_actoids[-1], test_assassin_rogue)
        first_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(first_turn_actoids[-1], test_assassin_rogue)
        first_turn_actoids.append(get_action(test_assassin_rogue))
        assert any(str(act).startswith("Cunning Dash") for act in first_turn_actoids)
        action_resolver.resolve_action(first_turn_actoids[-1], test_assassin_rogue)
        test_assassin_rogue.new_turn()
        second_turn_actoids = [get_action(test_assassin_rogue)]
        action_resolver.resolve_action(second_turn_actoids[-1], test_assassin_rogue)
        second_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(second_turn_actoids[-1], test_assassin_rogue)
        second_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(second_turn_actoids[-1], test_assassin_rogue)
        second_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(second_turn_actoids[-1], test_assassin_rogue)
        second_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(second_turn_actoids[-1], test_assassin_rogue)
        second_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(second_turn_actoids[-1], test_assassin_rogue)
        second_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(second_turn_actoids[-1], test_assassin_rogue)
        second_turn_actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(second_turn_actoids[-1], test_assassin_rogue)
        assert any(str(act).startswith("Cunning Hide") for act in second_turn_actoids)
        assert any(str(act).startswith("Shortbow") for act in second_turn_actoids)
        assert next(i for i, act in enumerate(second_turn_actoids) if str(act).startswith("Cunning Hide")) < next(i for i, act in enumerate(second_turn_actoids) if str(act).startswith("Shortbow"))
        assert any(str(act).startswith("(") for act in second_turn_actoids)
        assert list(filter(lambda act: str(act).startswith("Cunning Hide"), second_turn_actoids))[0].target is list(filter(lambda act: str(act).startswith("Shortbow"), second_turn_actoids))[0].target
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_rogue_cunning_dash(battle_map, teams, effect_tracker, test_assassin_rogue, test_bugbear, test_ogre, test_goblin):
    """
    Test scenario where the Rogue has three enemies nearby and no cover. The best option would be to use cunning dash.
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_assassin_rogue, test_bugbear, test_ogre, test_goblin]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_assassin_rogue, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    teams.add_combatant_to_team(test_ogre, Teams.Color.RED)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_assassin_rogue, np.array([7, 3]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([6, 1]))
    battle_map.set_combatant_coordinates(test_ogre, np.array([7, 0]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([9, 1]))
    battle_map.build_adjacency_matrix()
    test_bugbear.speed += 3  # Making him faster to incentivize the rogue to dash
    for combatant in combatants:
        combatant.curr_init = 0  # To prevent assassinate from crashing

    try:
        actoids = [get_action(test_assassin_rogue)]
        action_resolver.resolve_action(actoids[-1], test_assassin_rogue)
        actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(actoids[-1], test_assassin_rogue)
        actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(actoids[-1], test_assassin_rogue)
        actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(actoids[-1], test_assassin_rogue)
        actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(actoids[-1], test_assassin_rogue)
        actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(actoids[-1], test_assassin_rogue)
        actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(actoids[-1], test_assassin_rogue)
        actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(actoids[-1], test_assassin_rogue)
        actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(actoids[-1], test_assassin_rogue)
        actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(actoids[-1], test_assassin_rogue)
        actoids.append(get_action(test_assassin_rogue))
        action_resolver.resolve_action(actoids[-1], test_assassin_rogue)
        assert any(str(act).startswith("Cunning Dash") for act in actoids)
        assert any(str(act).startswith("Shortbow") for act in actoids)
        assert not any(str(act).startswith("Disengage") for act in actoids)
        assert sum(1 for act in actoids if str(act).startswith("(")) > 6
    except Exception as e:
        assert False, f"Raised an exception {e}"

@pytest.mark.slow
def test_ray_of_enfeeblement(battle_map, teams, effect_tracker, test_totem_barbarian, test_night_hag):
    """
    Test that Ray of Enfeeblement really does lower strength-based damage.
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_totem_barbarian, test_night_hag]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_night_hag, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([7, 4]))
    battle_map.set_combatant_coordinates(test_night_hag, np.array([7, 5]))
    battle_map.build_adjacency_matrix()
    FULL_HP = 1000
    test_night_hag.curr_hp = FULL_HP  # Making sure she doesn't die
    test_totem_barbarian.resources[BonusAction.TOTEM_RAGE].deplete_resource(ResourceDepletionLevel.FULLY_DEPLETED)

    try:
        pre_roe_actoids = []
        for _ in range(50):
            pre_roe_actoids.append(get_action(test_totem_barbarian))
            action_resolver.resolve_action(pre_roe_actoids[-1], test_totem_barbarian)
            pre_roe_actoids.append(get_action(test_totem_barbarian))
            action_resolver.resolve_action(pre_roe_actoids[-1], test_totem_barbarian)
            test_totem_barbarian.new_turn()
        pre_roe_dmg_dealt = FULL_HP - test_night_hag.curr_hp
        test_night_hag.curr_hp = FULL_HP

        roe_factory = None
        for af in test_night_hag.action_factories:
            if af[0] is Action.RAY_OF_ENFEEBLEMENT:
                roe_factory = af[1]
                break
        assert roe_factory, "No Ray of Enfeeblement factory found"
        roe_factory.to_hit = 20  # Making it a sure hit except natural 1
        roe = roe_factory.create(test_totem_barbarian)
        roe.activate()

        post_roe_actoids = []
        for _ in range(50):
            post_roe_actoids.append(get_action(test_totem_barbarian))
            action_resolver.resolve_action(post_roe_actoids[-1], test_totem_barbarian)
            if not test_night_hag.concentration_effect:
                roe.activate()
            post_roe_actoids.append(get_action(test_totem_barbarian))
            action_resolver.resolve_action(post_roe_actoids[-1], test_totem_barbarian)
            if not test_night_hag.concentration_effect:
                roe.activate()
            test_totem_barbarian.new_turn()
        post_roe_dmg_dealt = FULL_HP - test_night_hag.curr_hp

        tolerance = 0.15 * pre_roe_dmg_dealt
        assert abs(pre_roe_dmg_dealt - 2 * post_roe_dmg_dealt) <= tolerance
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_sleep_loss_of_concentration(battle_map, teams, effect_tracker, test_goblin, test_night_hag):
    """
    Test that targets put to sleep by the Sleep spell are awaken when the caster loses concentration.
    """
    CustomLogger(logging.WARNING)
    test_goblin_2 = copy.deepcopy(test_goblin)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_goblin, test_goblin_2, test_night_hag]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_goblin, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin_2, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_night_hag, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_goblin, np.array([4, 5]))
    battle_map.set_combatant_coordinates(test_goblin_2, np.array([5, 5]))
    battle_map.set_combatant_coordinates(test_night_hag, np.array([9, 5]))
    battle_map.build_adjacency_matrix()
    test_night_hag.saving_throws[SavingThrow.CON] = 1  # Making sure the concentration check fails
    try:
        sleep_factory = SleepFactory(Action.SLEEP, test_night_hag, test_night_hag.resources[Action.SLEEP])
        sleep = sleep_factory.create(np.array([4, 5]))
        action_resolver.resolve_action(sleep, test_night_hag)
        assert is_affected_by(test_goblin, Conditions.UNCONSCIOUS)
        assert is_affected_by(test_goblin_2, Conditions.UNCONSCIOUS)
        assert test_night_hag.concentration_effect is sleep

        test_night_hag.receive_dmg(50, DamageType.Force)

        assert not is_affected_by(test_goblin, Conditions.UNCONSCIOUS)
        assert not is_affected_by(test_goblin_2, Conditions.UNCONSCIOUS)
        assert test_night_hag.concentration_effect is None
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


def test_faerie_fire(battle_map, teams, effect_tracker, test_druid_lvl_1, test_fighter_lvl_1):
    """
    Based on a failure where the placement of Faerie Fire didn't make any sense. This was the basis for increasing
    the threat_radius of Faerie Fire so that the druid casts it from their current location.
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    battle_map.place_circular_element(np.array([6, 3]), Terrain.DIFFICULT_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([7, 2]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([7, 7]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    combatants = [test_druid_lvl_1, test_fighter_lvl_1]
    teams.add_combatant_to_team(test_fighter_lvl_1, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_druid_lvl_1, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_druid_lvl_1, np.array([0, 10]))
    battle_map.set_combatant_coordinates(test_fighter_lvl_1, np.array([13, 8]))
    battle_map.build_adjacency_matrix()

    actoid1 = get_action(test_druid_lvl_1)
    assert str(actoid1) == "Faerie Fire at [10  5]"


def test_menacing_attack_shares_ammo(battle_map, teams, effect_tracker, test_druid_lvl_1, test_battle_master_fighter_lvl_3):
    test_druid_lvl_1.curr_hp = 100  # Making sure they survive
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_druid_lvl_1, test_battle_master_fighter_lvl_3]
    teams.add_combatant_to_team(test_battle_master_fighter_lvl_3, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_druid_lvl_1, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_druid_lvl_1, np.array([5, 5]))
    battle_map.set_combatant_coordinates(test_battle_master_fighter_lvl_3, np.array([7, 5]))
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    assert id(test_battle_master_fighter_lvl_3.ammo['Handaxe']) == id(test_battle_master_fighter_lvl_3.ammo['Menacing Handaxe'])
    assert id(test_battle_master_fighter_lvl_3.ammo['Greatsword']) == id(test_battle_master_fighter_lvl_3.ammo['Menacing Greatsword'])
    ha = test_battle_master_fighter_lvl_3.handaxe[1].create(test_druid_lvl_1)

    assert test_battle_master_fighter_lvl_3.ammo['Handaxe'].get_resource() == 2
    assert test_battle_master_fighter_lvl_3.ammo['Menacing Handaxe'].get_resource() == 2
    action_resolver.resolve_action(ha, test_battle_master_fighter_lvl_3)
    assert test_battle_master_fighter_lvl_3.ammo['Handaxe'].get_resource() == 1
    assert test_battle_master_fighter_lvl_3.ammo['Menacing Handaxe'].get_resource() == 1

    # Find the Menacing Handaxe factory
    mha_factory = None
    for af in test_battle_master_fighter_lvl_3.action_factories:
        if str(af[1]) == "Menacing Handaxe AttackFactory":
            mha_factory = af[1]
            break
    assert mha_factory is not None
    test_battle_master_fighter_lvl_3.new_turn()
    mha = mha_factory.create(test_druid_lvl_1)
    action_resolver.resolve_action(mha, test_battle_master_fighter_lvl_3)
    assert test_battle_master_fighter_lvl_3.ammo['Handaxe'].get_resource() == 0
    assert test_battle_master_fighter_lvl_3.ammo['Menacing Handaxe'].get_resource() == 0


def test_lay_on_hands(battle_map, teams, effect_tracker, test_paladin_lvl_1, test_druid_lvl_1, test_battle_master_fighter_lvl_3):
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_paladin_lvl_1, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_battle_master_fighter_lvl_3, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_druid_lvl_1, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(test_paladin_lvl_1, np.array([5, 5]))
    battle_map.set_combatant_coordinates(test_druid_lvl_1, np.array([7, 5]))
    battle_map.set_combatant_coordinates(test_battle_master_fighter_lvl_3, np.array([14, 5]))

    loh_factory = None
    for af in test_paladin_lvl_1.action_factories:
        if str(af[1]) == "LayOnHandsFactory":
            loh_factory = af[1]
            break
    assert loh_factory is not None

    test_druid_lvl_1.curr_hp = test_druid_lvl_1.max_hp - 1
    all_loh = loh_factory.create_all()
    assert len(all_loh) == 1
    assert all_loh[0].hp_amount == 1

    test_druid_lvl_1.curr_hp = test_druid_lvl_1.max_hp - 4
    all_loh = loh_factory.create_all()
    assert len(all_loh) == 1
    assert all_loh[0].hp_amount == 4

    test_druid_lvl_1.curr_hp = test_druid_lvl_1.max_hp - 5
    all_loh = loh_factory.create_all()
    assert len(all_loh) == 1
    assert all_loh[0].hp_amount == 5

    # The pool size if the limit here
    test_druid_lvl_1.curr_hp = test_druid_lvl_1.max_hp - 6
    all_loh = loh_factory.create_all()
    assert len(all_loh) == 1
    assert all_loh[0].hp_amount == 5

    test_druid_lvl_1.curr_hp = test_druid_lvl_1.max_hp - 6
    test_paladin_lvl_1.resources[Action.LAY_ON_HANDS].set_resource(10)
    all_loh = loh_factory.create_all()
    assert len(all_loh) == 2
    assert all_loh[0].hp_amount == 5
    assert all_loh[1].hp_amount == 6

    test_druid_lvl_1.curr_hp = test_druid_lvl_1.max_hp - 10
    test_paladin_lvl_1.resources[Action.LAY_ON_HANDS].set_resource(10)
    all_loh = loh_factory.create_all()
    assert len(all_loh) == 2
    assert all_loh[0].hp_amount == 5
    assert all_loh[1].hp_amount == 10

    # Now two possible targets
    test_battle_master_fighter_lvl_3.curr_hp = test_battle_master_fighter_lvl_3.max_hp - 3
    test_druid_lvl_1.curr_hp = test_druid_lvl_1.max_hp - 10
    test_paladin_lvl_1.resources[Action.LAY_ON_HANDS].set_resource(10)
    all_loh = loh_factory.create_all()
    assert len(all_loh) == 3
    assert all_loh[0].hp_amount == 3
    assert all_loh[1].hp_amount == 5
    assert all_loh[2].hp_amount == 10

    test_paladin_lvl_1.resources[Action.LAY_ON_HANDS].set_resource(1)
    all_loh = loh_factory.create_all()
    assert len(all_loh) == 2
    assert all_loh[0].hp_amount == 1
    assert all_loh[1].hp_amount == 1


def test_conic_breath_weapon_placement(battle_map, teams, effect_tracker, test_young_green_dragon, test_skeleton, test_bugbear, test_hobgoblin):
    """ This test is based on an error scenario encountered during testing. We assert that given the layout of obstacles
    and enemies, there's no available coordinates for the selected breath origin."""
    test_bugbear_2 = copy.deepcopy(test_bugbear)
    test_hobgoblin_2 = copy.deepcopy(test_hobgoblin)
    battle_map.place_circular_element(np.array([8, 7]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([14, 8]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    battle_map.place_circular_element(np.array([11, 4]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    battle_map.place_circular_element(np.array([12, 2]), Terrain.IMPASSABLE_TERRAIN, radius=0)
    teams.add_combatant_to_team(test_young_green_dragon, Teams.Color.RED)
    teams.add_combatant_to_team(test_skeleton, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_bugbear_2, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_hobgoblin, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_hobgoblin_2, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(test_young_green_dragon, np.array([10, 9]))
    battle_map.set_combatant_coordinates(test_skeleton, np.array([12, 8]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([11, 8]))
    battle_map.set_combatant_coordinates(test_bugbear_2, np.array([8, 11]))
    battle_map.set_combatant_coordinates(test_hobgoblin, np.array([1, 5]))
    battle_map.set_combatant_coordinates(test_hobgoblin_2, np.array([6, 0]))
    battle_map.build_adjacency_matrix()
    distances, shortest_paths = battle_map.calc_dijkstra(test_young_green_dragon)
    test_young_green_dragon.shortest_paths_cache = shortest_paths

    breath_factory = None
    for af in test_young_green_dragon.action_factories:
        if str(af[1]) == "Poison BreathFactory":
            breath_factory = af[1]
            break
    assert breath_factory is not None
    all_breaths = breath_factory.create_all()
    failing_instance_index = None
    for idx, breath in enumerate(all_breaths):
        if str(breath) == "Poison Breath from (9, 8) at 60.4 deg":
            failing_instance_index = idx
            break
    assert failing_instance_index is not None
    battle_map.clear_caches()
    eligible_coords = all_breaths[failing_instance_index].get_eligible_coords(distances, shortest_paths)
    assert not eligible_coords


def test_conic_breath_weapon_placement_into_an_obstacle(battle_map, teams, effect_tracker, test_green_dragon_wyrmling, test_skeleton):
    battle_map.place_circular_element(np.array([8, 7]), Terrain.IMPASSABLE_TERRAIN, radius=1)
    teams.add_combatant_to_team(test_green_dragon_wyrmling, Teams.Color.RED)
    teams.add_combatant_to_team(test_skeleton, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(test_green_dragon_wyrmling, np.array([10, 9]))
    battle_map.set_combatant_coordinates(test_skeleton, np.array([12, 8]))
    battle_map.build_adjacency_matrix()
    distances, shortest_paths = battle_map.calc_dijkstra(test_green_dragon_wyrmling)

    breath_factory = None
    for af in test_green_dragon_wyrmling.action_factories:
        if str(af[1]) == "Poison BreathFactory":
            breath_factory = af[1]
            break
    assert breath_factory is not None
    breath = breath_factory.create((8, 7))
    battle_map.clear_caches()
    eligible_coords = breath.get_eligible_coords(distances, shortest_paths)
    assert not eligible_coords


def test_second_wind(battle_map, teams, effect_tracker, test_fighter_lvl_1, test_skeleton, test_goblin):
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_fighter_lvl_1, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_skeleton, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_fighter_lvl_1, np.array([3, 3]))
    battle_map.set_combatant_coordinates(test_skeleton, np.array([5, 3]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([2, 3]))
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_fighter_lvl_1, test_skeleton, test_goblin]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    test_fighter_lvl_1.curr_hp = 3  # Make sure enough HP are missing
    try:
        actoids = [get_action(test_fighter_lvl_1)]
        action_resolver.resolve_action(actoids[-1], test_fighter_lvl_1)
        actoids.append(get_action(test_fighter_lvl_1))
        action_resolver.resolve_action(actoids[1], test_fighter_lvl_1)
        assert any(str(act).startswith("Greatsword") for act in actoids)
        assert any(str(act).startswith("Second Wind") for act in actoids)
    except Exception as e:
        assert False, f"Raised an exception {e}"
