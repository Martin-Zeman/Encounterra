import numpy as np
import pytest

from simulator.action_resolver import ActionResolver
from simulator.actions.action_types import Action
from simulator.logging.custom_logger import CustomLogger, LogLevel
from simulator.spells.haste import HasteFactory
from simulator.teams import Teams
from simulator.test.fixtures import combatant1, combatant2, combatant3, combatant4, combatant5, combatant6, teams, effect_tracker, battle_map

def test_haste(battle_map, teams, effect_tracker, combatant1, combatant3, combatant4):
    """
    We assert that a hasted bugbear utilizes both its regular attack and hasted attack independently, although each attack must be used
    once.
    """
    CustomLogger(LogLevel.WARNING)

    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    teams.add_combatant_to_team(combatant1, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(combatant3, Teams.Color.BLUE)  # For the log coloring...
    teams.add_combatant_to_team(combatant4, Teams.Color.RED)  # For the log coloring...
    battle_map.set_combatant_coordinates(combatant1, np.array([0, 0]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(combatant3, np.array([4, 4]))  # Have to set it for fireball placement
    battle_map.set_combatant_coordinates(combatant4, np.array([5, 4]))  # Have to set it for fireball placement
    battle_map.build_adjacency_matrix()
    battle_map.set_effect_tracker(effect_tracker)
    effect_tracker.set_battle_map(battle_map)
    combatants = [combatant1, combatant3, combatant4]
    action_resolver = ActionResolver(combatants, teams, battle_map, effect_tracker)

    try:
        hf = HasteFactory(Action.HASTE, combatant1, effect_tracker)
        haste = hf.create(combatant3)
        action_resolver.resolve_action(haste, combatant1)

        actoid1 = combatant3.get_action(battle_map)
        action_resolver.resolve_action(actoid1, combatant3)
        actoid2 = combatant3.get_action(battle_map)
        assert str(actoid1) == "Morningstar on TotemBarbarian5Lvl" or str(actoid2) == "Morningstar on TotemBarbarian5Lvl"
        assert str(actoid1) == "Hasted Morningstar on TotemBarbarian5Lvl" or str(actoid2) == "Hasted Morningstar on TotemBarbarian5Lvl"
        action_resolver.resolve_action(actoid2, combatant3)
        actoid3 = combatant3.get_action(battle_map)
        assert str(actoid3) == "None"
    except Exception as e:
        assert False, f"Raised an exception {e}"