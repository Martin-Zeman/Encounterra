import copy
import logging
import pstats
import numpy as np

from ..action_resolver import ActionResolver
from ..actions.action_dag import generate_proto_dag
from ..logging.custom_logger import CustomLogger
from ..spells.fireball import Fireball
from ..spells.twinned_firebolt import TwinnedFirebolt
from ..teams import Teams
from ..test.fixtures import test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, test_totem_barbarian, test_stone_giant, test_ogre, teams, effect_tracker, battle_map
from ..actions.action_selector import build_action_dag, get_action
import types
import cProfile


def test_build_action_dag_misty_step_and_firebolt(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_goblin, test_bugbear):
    CustomLogger(logging.WARNING)
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([1, 3]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(test_goblin, np.array([10, 10]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(test_bugbear, np.array([3, 4]))  # Have to set it for fireball placement

    # fsm, transition_mapping = generate_proto_dag(test_draconic_sorcerer_5lvl)
    # assert fsm.state == '0'
    # fsm.get_graph().draw('state_diagram_faurung_pre_coords.png', prog='dot')
    # Pre-calculate Dijkstra for the combatant
    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    # get_aoe_and_aoo_threat_for_increment.cache_clear()
    fsm, transition_name_to_action = generate_proto_dag(test_draconic_sorcerer_5lvl)
    dag, _, _ = build_action_dag(test_draconic_sorcerer_5lvl, fsm, transition_name_to_action, distances, shortest_paths)
    # dfs.get_graph().draw('state_diagram_faurung_with_coords',format='svg', prog='dot')

    # Tests the Misty Step movement + Firebolt
    assert dag.state == '0'
    transitions = dag.get_available_transitions()
    assert "Dodge of Draconic Sorcerer 5. Level 1_1" in transitions
    assert "Disengage of Draconic Sorcerer 5. Level 1_1" in transitions
    assert "ms_(7, 3)" in transitions
    assert "ms_(2, 3)" in transitions
    assert "m_(7, 3)" in transitions
    dag.trigger("ms_(2, 3)")
    transitions = dag.get_available_transitions()
    assert "Staff of Defence on Goblin 1_1" not in transitions  # Test that Misty Step actions are also prepended with movement
    assert "Staff of Defence on Bugbear 1_2" in transitions  # Test that Misty Step actions are also prepended with movement
    assert "Firebolt on Goblin 1_2" in transitions
    assert "Firebolt on Bugbear 1_2" in transitions
    assert "Twinned Firebolt on Goblin 1 and Bugbear 1_2" in transitions
    assert "Dodge of Draconic Sorcerer 5. Level 1_2" not in transitions # Even though it's possible, we don't support dodge after Misty Step, as it's very niche
    assert "Disengage of Draconic Sorcerer 5. Level 1_2" not in transitions # Even though it's possible, we don't support dodge after Misty Step, as it's very niche
    dag.trigger("Firebolt on Goblin 1_2")
    assert len(dag.get_available_transitions()) == 0


def test_build_action_dag_movement_and_quickened_fireball(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_goblin, test_bugbear):
        battle_map.build_adjacency_matrix()
        battle_map.set_effect_tracker(effect_tracker)
        teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
        teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
        # teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
        battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([1, 3]))
        battle_map.set_combatant_coordinates(test_goblin, np.array([10, 10]))
        # battle_map.set_combatant_coordinates(test_bugbear, np.array([2, 3]))

        # Pre-calculate Dijkstra for the combatant
        distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
        # get_aoe_and_aoo_threat_for_increment.cache_clear()
        fsm, transition_name_to_action = generate_proto_dag(test_draconic_sorcerer_5lvl)
        dag, _, _ = build_action_dag(test_draconic_sorcerer_5lvl, fsm, transition_name_to_action, distances, shortest_paths)
        transitions = dag.get_available_transitions()
        # Tests regular movement + quickened fireball
        assert dag.state == '0'
        assert 'Dodge of Draconic Sorcerer 5. Level 1_1' in transitions
        assert 'Disengage of Draconic Sorcerer 5. Level 1_1' in transitions
        dag.trigger("m_(2, 3)")
        transitions = dag.get_available_transitions()
        # Check that we have all the action (except for the Staff attack) available
        assert 'Quickened Fireball at [ 6 10]_1' in transitions
        assert 'Quickened Firebolt on Goblin 1_1' in transitions
        assert 'Quickened Haste on Draconic Sorcerer 5. Level 1_1' in transitions
        assert 'Fireball at [ 6 10]_1' in transitions
        assert 'Firebolt on Goblin 1_1' in transitions
        assert 'Haste on Draconic Sorcerer 5. Level 1_1' in transitions
        assert 'Dodge of Draconic Sorcerer 5. Level 1_1' not in transitions  # Once you do a regular move, Dodge should not be available
        assert 'Disengage of Draconic Sorcerer 5. Level 1_1' not in transitions  # Once you do a regular move, Disengage should not be available
        dag.trigger("Quickened Fireball at [ 6 10]_1")
        transitions = dag.get_available_transitions()
        # For the second action, coordinates are not taken into account
        assert 'Staff of Defence on Goblin 1_2' in transitions
        assert 'Firebolt on Goblin 1_2' in transitions
        assert 'Dodge of Draconic Sorcerer 5. Level 1_2' not in transitions
        assert 'Disengage of Draconic Sorcerer 5. Level 1_2' not in transitions


def test_build_action_dag_movement_and_fireball(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_goblin, test_bugbear):
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    # teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([1, 3]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([10, 10]))
    # battle_map.set_combatant_coordinates(test_bugbear, np.array([2, 3]))  # Have to set it for fireball placement

    # Pre-calculate Dijkstra for the combatant
    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    # get_aoe_and_aoo_threat_for_increment.cache_clear()
    fsm, transition_name_to_action = generate_proto_dag(test_draconic_sorcerer_5lvl)
    dag, _, _ = build_action_dag(test_draconic_sorcerer_5lvl, fsm, transition_name_to_action, distances, shortest_paths)
    # Tests regular movement + fireball
    assert dag.state == '0'
    dag.trigger("m_(2, 3)")
    transitions = dag.get_available_transitions()
    # Check that we have all the action (except for the Staff attack) available
    assert 'Quickened Fireball at [ 6 10]_1' in transitions
    assert 'Quickened Firebolt on Goblin 1_1' in transitions
    assert 'Quickened Haste on Draconic Sorcerer 5. Level 1_1' in transitions
    assert 'Fireball at [ 6 10]_1' in transitions
    assert 'Firebolt on Goblin 1_1' in transitions
    assert 'Haste on Draconic Sorcerer 5. Level 1_1' in transitions
    assert 'Dodge of Draconic Sorcerer 5. Level 1_1' not in transitions  # Once you do a regular move, Dodge should not be available
    assert 'Disengage of Draconic Sorcerer 5. Level 1_1' not in transitions  # Once you do a regular move, Disengage should not be available
    dag.trigger("Fireball at [ 6 10]_1")
    transitions = dag.get_available_transitions()
    # For the second action, coordinates are not taken into account
    assert 'Quickened Firebolt on Goblin 1_2' in transitions


def test_build_action_dag_movement_and_staff_attack(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_goblin, test_bugbear):
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    # teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([1, 3]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([10, 10]))
    # battle_map.set_combatant_coordinates(test_bugbear, np.array([2, 3]))

    # Pre-calculate Dijkstra for the combatant
    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    # get_aoe_and_aoo_threat_for_increment.cache_clear()
    fsm, transition_name_to_action = generate_proto_dag(test_draconic_sorcerer_5lvl)
    dag, _, _ = build_action_dag(test_draconic_sorcerer_5lvl, fsm, transition_name_to_action, distances, shortest_paths)
    # Tests regular movement + staff of defence attack
    assert dag.state == '0'
    dag.trigger("m_(9, 10)")
    transitions = dag.get_available_transitions()
    # Check that we have all the action (except for the Staff attack) available
    assert 'Quickened Fireball at [ 6 10]_1' in transitions
    assert 'Quickened Firebolt on Goblin 1_1' in transitions
    assert 'Quickened Haste on Draconic Sorcerer 5. Level 1_1' in transitions
    assert 'Fireball at [ 6 10]_1' in transitions
    assert 'Firebolt on Goblin 1_1' in transitions
    assert 'Haste on Draconic Sorcerer 5. Level 1_1' in transitions
    assert 'Staff of Defence on Goblin 1_1' in transitions
    assert 'Dodge of Draconic Sorcerer 5. Level 1_1' not in transitions  # Once you do a regular move, Dodge should not be available
    assert 'Disengage of Draconic Sorcerer 5. Level 1_1' not in transitions  # Once you do a regular move, Disengage should not be available
    dag.trigger("Staff of Defence on Goblin 1_1")
    transitions = dag.get_available_transitions()
    # For the second action, coordinates are not taken into account, but Dodge is included
    assert 'Quickened Haste on Draconic Sorcerer 5. Level 1_2' in transitions
    assert 'Quickened Fireball at [ 6 10]_2' in transitions
    assert 'Quickened Firebolt on Goblin 1_2' in transitions


def test_build_action_dag_misty_step_and_staff_attack(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_goblin,
                                                      test_bugbear):
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    # teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([1, 3]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([10, 10]))
    # battle_map.set_combatant_coordinates(test_bugbear, np.array([2, 3]))

    # Pre-calculate Dijkstra for the combatant
    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    # get_aoe_and_aoo_threat_for_increment.cache_clear()
    fsm, transition_name_to_action = generate_proto_dag(test_draconic_sorcerer_5lvl)
    dag, _, _ = build_action_dag(test_draconic_sorcerer_5lvl, fsm, transition_name_to_action, distances, shortest_paths)
    # Tests Misty Step movement + staff of defence attack
    assert dag.state == '0'
    dag.trigger("ms_(9, 10)")
    transitions = dag.get_available_transitions()
    # Check that we have all the action (except for the Staff attack) available
    assert "Staff of Defence on Goblin 1_2" in transitions  # Test that Misty Step actions are also prepended with movement
    assert "Firebolt on Goblin 1_2" in transitions
    dag.trigger("Staff of Defence on Goblin 1_2")
    assert len(dag.get_available_transitions()) == 0


def test_build_action_dag_dodge_and_movement_and_quickened_spell(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_goblin, test_bugbear):
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    # teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([1, 3]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([10, 10]))
    # battle_map.set_combatant_coordinates(test_bugbear, np.array([2, 3]))

    # Pre-calculate Dijkstra for the combatant
    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    # get_aoe_and_aoo_threat_for_increment.cache_clear()
    fsm, transition_name_to_action = generate_proto_dag(test_draconic_sorcerer_5lvl)
    dag, _, _ = build_action_dag(test_draconic_sorcerer_5lvl, fsm, transition_name_to_action, distances, shortest_paths)
    # Tests Dodge + movement + a quickened spell
    assert dag.state == '0'
    dag.trigger("Dodge of Draconic Sorcerer 5. Level 1_1")
    assert dag.state == 'Dodged'
    transitions = dag.get_available_transitions()
    assert "do_(7, 3)" in transitions
    assert "ms_(2, 3)" not in transitions  # Even though it's possible, we don't support Misty Step after Dodge, as it's very niche
    dag.trigger("do_(7, 3)")
    transitions = dag.get_available_transitions()
    assert 'Quickened Fireball at [ 6 10]_2' in transitions
    assert 'Quickened Firebolt on Goblin 1_2' in transitions
    assert 'Quickened Haste on Draconic Sorcerer 5. Level 1_2' in transitions
    dag.trigger("Quickened Haste on Draconic Sorcerer 5. Level 1_2")
    assert len(dag.get_available_transitions()) == 0


def test_build_action_dag_disengage_and_movement_and_quickened_spell(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_goblin, test_bugbear):
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    # teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([1, 3]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([10, 10]))
    # battle_map.set_combatant_coordinates(test_bugbear, np.array([2, 3]))

    # Pre-calculate Dijkstra for the combatant
    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    # get_aoe_and_aoo_threat_for_increment.cache_clear()
    fsm, transition_name_to_action = generate_proto_dag(test_draconic_sorcerer_5lvl)
    dag, _, _ = build_action_dag(test_draconic_sorcerer_5lvl, fsm, transition_name_to_action, distances, shortest_paths)
    # Tests Disengage + movement + a quickened spell
    assert dag.state == '0'
    dag.trigger("Disengage of Draconic Sorcerer 5. Level 1_1")
    # assert dag.state == 'Disengaged'
    transitions = dag.get_available_transitions()
    assert "di_(5, 3)" in transitions
    assert "ms_(2, 3)" not in transitions  # Even though it's possible, we don't support Misty Step after Dodge, as it doesn't make muche sense
    dag.trigger("di_(5, 3)")
    transitions = dag.get_available_transitions()
    assert 'Quickened Fireball at [ 6 10]_2' in transitions
    assert 'Quickened Firebolt on Goblin 1_2' in transitions
    assert 'Quickened Haste on Draconic Sorcerer 5. Level 1_2' in transitions
    dag.trigger("Quickened Firebolt on Goblin 1_2")
    assert len(dag.get_available_transitions()) == 0


def test_calculate_action_plan_twin_firebolt_and_fireball(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_goblin, test_bugbear):
    CustomLogger(logging.WARNING)
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([1, 3]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(test_goblin, np.array([10, 10]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(test_bugbear, np.array([2, 4]))  # Have to set it for fireball placement

    class DummyEffect:
        def deactivate(self):
            test_draconic_sorcerer_5lvl.break_concentration()

        def deactivate_for_combatant(self, combatant):
            assert False

        def is_affecting(self, combatant):
            return False
    dummy_effect = DummyEffect()
    test_draconic_sorcerer_5lvl.concentration_effect = dummy_effect  # Make sure the sorcerer won't opt for Hold Person

    distances, shortest_paths = battle_map.calc_dijkstra(test_draconic_sorcerer_5lvl)
    test_draconic_sorcerer_5lvl.shortest_paths_cache = shortest_paths
    action_plan = test_draconic_sorcerer_5lvl.calculate_action_plan(distances, shortest_paths)
    assert any(isinstance(obj, TwinnedFirebolt) for obj in action_plan)
    assert any(isinstance(obj, Fireball) for obj in action_plan)  # Quickened version


def test_rage_before_attack(battle_map, teams, effect_tracker, test_bugbear, test_totem_barbarian):
    """
    We assert that the barbarian rages before doing anything else.
    """
    CustomLogger(logging.WARNING)

    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 4]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([13, 4]))  # Have to set it for fireball placement
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_bugbear, test_totem_barbarian]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)

    try:
        actoid1 = get_action(test_totem_barbarian)
        assert str(actoid1) == 'Totem Rage of Totem Barbarian 5. Level 1'
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
        assert str(actoid10) == 'Reckless Attack at Bugbear 1'
        action_resolver.resolve_action(actoid10, test_totem_barbarian)
        actoid11 = get_action(test_totem_barbarian)
        assert str(actoid11) == 'Reckless Attack at Bugbear 1'
        action_resolver.resolve_action(actoid11, test_totem_barbarian)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_bugbear_going_into_melee(battle_map, teams, effect_tracker, test_bugbear, test_totem_barbarian):
    """
    It had occured during testing that the bugbear would opt for staying at range and throw javelins rather than go in melee range
    which is not desirable.
    """
    CustomLogger(logging.WARNING)

    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 4]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([11, 4]))  # Have to set it for fireball placement
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_bugbear, test_totem_barbarian]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)

    try:
        actoid1 = get_action(test_bugbear)
        action_resolver.resolve_action(actoid1, test_bugbear)
        actoid2 = get_action(test_bugbear)
        action_resolver.resolve_action(actoid2, test_bugbear)
        actoid3 = get_action(test_bugbear)
        action_resolver.resolve_action(actoid3, test_bugbear)
        actoid4 = get_action(test_bugbear)
        action_resolver.resolve_action(actoid4, test_bugbear)
        actoid5 = get_action(test_bugbear)
        action_resolver.resolve_action(actoid5, test_bugbear)
        actoid6 = get_action(test_bugbear)
        action_resolver.resolve_action(actoid6, test_bugbear)
        actoid7 = get_action(test_bugbear)
        assert str(actoid7) == "Morningstar on Totem Barbarian 5. Level 1"
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_goblin_using_cunning_disengage(battle_map, teams, effect_tracker, test_goblin, test_bugbear):
    """
    We assert that the goblin first uses his cunning disengage to first get away and then shoots his bow.
    """
    CustomLogger(logging.WARNING)
    test_bugbear_2 = copy.deepcopy(test_bugbear)
    battle_map.set_effect_tracker(effect_tracker)
    teams.add_combatant_to_team(test_goblin, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)  # For the log coloring...
    teams.add_combatant_to_team(test_bugbear_2, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(test_goblin, np.array([6, 4]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(test_bugbear, np.array([7, 4]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(test_bugbear_2, np.array([8, 4]))  # Have to set it for fireball placement
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_goblin, test_bugbear, test_bugbear_2]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)

    try:
        actoid1 = get_action(test_goblin)
        assert str(actoid1) == "Cunning Disengage of Goblin 1"
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
        actoid7 = get_action(test_goblin)
        action_resolver.resolve_action(actoid7, test_goblin)
        actoid8 = get_action(test_goblin)
        assert str(actoid8) == "Shortbow on Bugbear 1"
    except Exception as e:
        assert False, f"Raised an exception {e}"
