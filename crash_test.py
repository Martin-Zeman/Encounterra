import logging
import pickle

from simulator.actions.action_selector import get_action
from simulator.battle_map import Map
from simulator.logging.custom_logger import CustomLogger
from simulator.session import Session

TIMESTAMP = "1712060998"


def unify_combatants(session, battle_map):
    map_combatants_keys = list(battle_map.combatant_coordinate_cache.keys())

    for combatant in session.combatants:
        for map_combatant_key in map_combatants_keys:
            if combatant.name == map_combatant_key.name:
                battle_map.combatant_coordinate_cache[combatant] = battle_map.combatant_coordinate_cache.pop(map_combatant_key)
                break
    # Unify combatants in the grid
    for row in battle_map.grid:
        for grid_square in row:
            if grid_square.combatant:
                for combatant in session.combatants:
                    if grid_square.combatant.name == combatant.name:
                        grid_square.combatant = combatant
                        break


def test_crash():
    """
    Deserializes error objects after:
    'NoneType' object is not iterable
    """
    CustomLogger(logging.WARNING)
    with open(f'simulator/test/serialized_objects/battle_map_data_{TIMESTAMP}.pkl', 'rb') as f:
        map_data = pickle.load(f)
        Map.deserialize_data(map_data)

    # Load the session
    with open(f'simulator/test/serialized_objects/session_{TIMESTAMP}.pkl', 'rb') as f:
        session_data = pickle.load(f)
        session = Session()
        session.deserialize_data(session_data)
    battle_map = Map.get()
    battle_map.effect_tracker = session.effect_tracker
    battle_map.teams = session.teams
    unify_combatants(session, Map.get())
    actoid = get_action(session.combatants[session.combatants.index(session.round_manager.curr_combatant)])
    session.round_manager.action_resolver.resolve_action(actoid, session.combatants[1])
