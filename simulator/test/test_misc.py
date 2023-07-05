import numpy as np
import pytest

from simulator.abilities.wildshape import WildshapeFactory
from simulator.action_resolver import ActionResolver
from simulator.actions.action_selector import get_action
from simulator.actions.action_types import BonusAction, Action
from simulator.battle_map import Map
from simulator.combatants.giant_toad import GiantToad
from simulator.logging.custom_logger import CustomLogger, LogLevel
from simulator.misc import Conditions, DamageType
from simulator.spells.flaming_sphere import FlamingSphereFactory
from simulator.teams import Teams
from simulator.test.fixtures import test_moon_druid, test_draconic_sorcerer_5lvl, teams, effect_tracker, battle_map
from simulator.utils.utils import preallocate_wildshape_forms

def test_concentration_basic(battle_map, teams, effect_tracker, test_moon_druid, test_draconic_sorcerer_5lvl):
    """
    Tests the basic concentration mechanic functionality
    """
    CustomLogger(LogLevel.WARNING)
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

    fs_factory = FlamingSphereFactory(Action.FLAMING_SPHERE, test_moon_druid.dc, test_moon_druid)
    fs = fs_factory.create(np.array((6, 13)))

    test_moon_druid.curr_hp = 200  # Make sure we can deal huge damage to it and have it survive

    try:
        action_resolver.resolve_action(fs, test_moon_druid)
        assert test_moon_druid.concentration_effect is not None
        test_moon_druid.receive_dmg(50, DamageType.Slashing)  # Only a nat 20 can save it
        if not test_moon_druid.concentration_effect:
            assert len(Map.get().effect_tracker.get_effect_by_initiator(test_moon_druid)) == 0

    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_concentration_two_attacks_wildshaped(battle_map, teams, effect_tracker, test_moon_druid, test_draconic_sorcerer_5lvl):
    """
    Tests the concentration mechanic functionality in combination with wildshape
    """
    CustomLogger(LogLevel.WARNING)
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
    fs_factory = FlamingSphereFactory(Action.FLAMING_SPHERE, test_moon_druid.dc, test_moon_druid)
    fs = fs_factory.create(np.array((6, 13)))

    test_moon_druid.curr_hp = 200  # Make sure we can deal huge damage to it and have it survive

    try:
        action_resolver.resolve_action(fs, test_moon_druid)
        action_resolver.resolve_action(ws, test_moon_druid)
        test_moon_druid.get_current_form().curr_hp = 200
        assert test_moon_druid.get_current_form().concentration_effect is not None
        assert test_moon_druid.concentration_effect is not None
        test_moon_druid.get_current_form().receive_dmg(50, DamageType.Slashing)  # Only a nat 20 can save it
        if not test_moon_druid.get_current_form().concentration_effect:
            assert not test_moon_druid.concentration_effect
            assert len(Map.get().effect_tracker.get_effect_by_initiator(test_moon_druid)) == 0
            test_moon_druid.get_current_form().receive_dmg(1, DamageType.Slashing)
            assert len(Map.get().effect_tracker.get_effect_by_initiator(test_moon_druid)) == 0

    except Exception as e:
        assert False, f"Raised an exception {e}"