import logging

import numpy as np
import pytest

from ..abilities.wildshape import WildshapeFactory
from ..action_resolver import ActionResolver
from ..actions.action_selector import get_action
from ..actions.action_types import BonusAction, Action
from ..battle_map import Map
from ..combatants.giant_toad import GiantToad
from ..conditions import is_affected_by, Conditions
from ..effects.effect import EffectType
from ..logging.custom_logger import CustomLogger
from ..misc import DamageType
from ..spells.flaming_sphere import FlamingSphereFactory
from ..teams import Teams
from ..test.fixtures import test_moon_druid, test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, teams, effect_tracker, battle_map
from ..utils.utils import preallocate_wildshape_forms

def test_concentration_basic(battle_map, teams, effect_tracker, test_moon_druid, test_draconic_sorcerer_5lvl):
    """
    Tests the basic concentration mechanic functionality
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_moon_druid, test_draconic_sorcerer_5lvl]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_moon_druid, Teams.Color.RED)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([8, 13]))
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([8, 8]))
    test_moon_druid.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid, BonusAction.MOON_WILDSHAPE, test_moon_druid.wildshape_factory[1])
    battle_map.build_adjacency_matrix()
    _, shortest_paths = battle_map.calc_dijkstra(test_moon_druid)
    test_moon_druid.shortest_paths_cache = shortest_paths

    fs_factory = FlamingSphereFactory(test_moon_druid.dc, Action.FLAMING_SPHERE, test_moon_druid, test_moon_druid.spellslots)
    fs = fs_factory.create(np.array((6, 13)))

    test_moon_druid.curr_hp = 200  # Make sure we can deal huge damage to it and have it survive

    try:
        action_resolver.resolve_action(fs, test_moon_druid)
        assert test_moon_druid.concentration_effect is not None
        test_moon_druid.receive_dmg(50, DamageType.Slashing)  # Only a nat 20 can save it
        if not test_moon_druid.concentration_effect:
            assert len(Map.get().effect_tracker.get_effects_by_initiator(test_moon_druid)) == 0

    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_concentration_two_attacks_wildshaped(battle_map, teams, effect_tracker, test_moon_druid, test_draconic_sorcerer_5lvl):
    """
    Tests the concentration mechanic functionality in combination with wildshape
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_moon_druid, test_draconic_sorcerer_5lvl]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_moon_druid, Teams.Color.RED)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([8, 13]))
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([8, 8]))
    test_moon_druid.available_wildshape_forms = preallocate_wildshape_forms(test_moon_druid, BonusAction.MOON_WILDSHAPE, test_moon_druid.wildshape_factory[1])
    battle_map.build_adjacency_matrix()
    _, shortest_paths = battle_map.calc_dijkstra(test_moon_druid)
    test_moon_druid.shortest_paths_cache = shortest_paths

    ws_factory = WildshapeFactory(test_moon_druid, BonusAction.MOON_WILDSHAPE)
    ws = ws_factory.create(GiantToad)
    fs_factory = FlamingSphereFactory(test_moon_druid.dc, Action.FLAMING_SPHERE, test_moon_druid, test_moon_druid.spellslots)
    fs = fs_factory.create(np.array((6, 13)))

    test_moon_druid.curr_hp = 200  # Make sure we can deal huge damage to it and have it survive

    try:
        action_resolver.resolve_action(fs, test_moon_druid)
        action_resolver.resolve_action(ws, test_moon_druid)
        assert len(Map.get().effect_tracker.get_effects_by_initiator(test_moon_druid)) == 2
        test_moon_druid.get_current_form().curr_hp = 200
        assert test_moon_druid.get_current_form().concentration_effect is not None
        assert test_moon_druid.concentration_effect is not None
        test_moon_druid.get_current_form().receive_dmg(50, DamageType.Slashing)  # Only a nat 20 can save it
        if not test_moon_druid.get_current_form().concentration_effect:
            assert not test_moon_druid.concentration_effect
            assert len(Map.get().effect_tracker.get_effects_by_initiator(test_moon_druid)) == 1
            test_moon_druid.get_current_form().receive_dmg(1, DamageType.Slashing)
            assert len(Map.get().effect_tracker.get_effects_by_initiator(test_moon_druid)) == 1

    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_map_position_toggled_cache(battle_map, teams, effect_tracker, test_goblin, test_bugbear):
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(test_goblin, np.array([8, 13]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([8, 8]))
    battle_map.build_adjacency_matrix()

    shortbow = test_goblin.shortbow_attack[1].create(test_bugbear)
    threat_before = shortbow.calculate_threat()
    battle_map.move_combatant(test_goblin, np.array([8, 9]))
    threat_after = shortbow.calculate_threat()
    assert threat_before != threat_after

    battle_map.move_combatant(test_goblin, np.array([8, 13]))
    threat_after = shortbow.calculate_threat()
    assert threat_before == threat_after


def test_teams_get_surviving_teams(battle_map, teams, effect_tracker, test_moon_druid, test_bugbear):
    """
    We assert that get_surviving_teams behaves correctly when the last combatant standing is a wildshaped druid who
    just digested the last enemy
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

    try:
        actoid1 = get_action(test_moon_druid)
        assert test_moon_druid.curr_hp == 43
        assert str(actoid1) == "Wildshape of Moon Druid 5th LVL (1) into Giant Toad"
        action_resolver.resolve_action(actoid1, test_moon_druid)
        assert test_moon_druid.get_current_form() is not test_moon_druid
        assert test_moon_druid.current_wildshape_form is not None
        assert test_moon_druid.get_current_form().curr_hp == 39
        test_bugbear.curr_hp = 100  # Making sure it survives
        test_bugbear.ac = 0  # Making sure the toad hits
        test_moon_druid.new_turn()
        actoid2 = get_action(test_moon_druid)
        assert str(actoid2) == "Toad Bite on Bugbear (1)"
        action_resolver.resolve_action(actoid2, test_moon_druid)
        test_moon_druid.new_turn()
        actoid3 = get_action(test_moon_druid)
        assert str(actoid3) == "Toad Bite and Swallow on Bugbear (1)"
        action_resolver.resolve_action(actoid3, test_moon_druid)
        assert is_affected_by(test_bugbear, Conditions.SWALLOWED)
        test_bugbear.curr_hp = 1  # Making sure digestion kills it
        effect_tracker.start_of_turn(test_bugbear)
        assert not test_bugbear.is_alive()
        assert len(battle_map.teams.get_surviving_teams()) == 1
    except Exception as e:
        assert False, f"Exception occurred: {e}"
