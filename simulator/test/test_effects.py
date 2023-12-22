import logging

import numpy as np

from ..action_resolver import ActionResolver
from ..actions.action_types import Action
from ..conditions import is_affected_by, Conditions
from ..logging.custom_logger import CustomLogger
from ..misc import SavingThrow
from ..spells.twinned_hold_person import TwinnedHoldPersonFactory
from ..teams import Teams
from ..test.fixtures import test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, test_totem_barbarian, test_stone_giant,\
    test_ogre, test_moon_druid, test_giant_toad, teams, effect_tracker, battle_map, test_dragonclaw_cultist, test_brown_bear,\
    test_dire_wolf, test_assassin_rogue, test_draconic_sorcerer_3lvl, test_giant_constrictor_snake, test_twig_blight, \
    test_bandit_captain, test_sabertoother_tiger, test_berserker, test_evil_mage, test_commoner
from ..actions.action_selector import get_action


def test_independent_saves(battle_map, teams, effect_tracker, test_goblin, test_draconic_sorcerer_5lvl, test_bugbear):
    """
    Tests that combatants affected by effects that can be saved against independently again (.e.g at the end of their turn)
    behave correctly in terms of deletion and concentration
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_goblin, test_draconic_sorcerer_5lvl, test_bugbear]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_goblin, np.array([3, 5]))
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([5, 5]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([7, 5]))

    battle_map.build_adjacency_matrix()
    test_goblin.saving_throws[SavingThrow.WIS] = -20  # Making sure it fails expect for nat 20
    test_bugbear.saving_throws[SavingThrow.WIS] = -20  # Making sure it fails expect for nat 20

    twinned_hold_person_factory = TwinnedHoldPersonFactory(15, Action.TWINNED_HOLD_PERSON, test_draconic_sorcerer_5lvl, test_draconic_sorcerer_5lvl.spellslots)
    twinned_hold_person = twinned_hold_person_factory.create([test_goblin, test_bugbear])

    try:
        action_resolver.resolve_action(twinned_hold_person, test_draconic_sorcerer_5lvl)

        assert is_affected_by(test_goblin, Conditions.PARALYZED)
        assert is_affected_by(test_bugbear, Conditions.PARALYZED)
        assert test_draconic_sorcerer_5lvl.concentration_effect is twinned_hold_person

        test_goblin.saving_throws[SavingThrow.WIS] = 20  # Making sure it succeeds expect for nat 1
        effect_tracker.end_of_turn(test_goblin)
        assert not is_affected_by(test_goblin, Conditions.PARALYZED)
        assert is_affected_by(test_bugbear, Conditions.PARALYZED)
        assert test_draconic_sorcerer_5lvl.concentration_effect is twinned_hold_person
        assert twinned_hold_person in effect_tracker.effects


        test_bugbear.saving_throws[SavingThrow.WIS] = 20  # Making sure it succeeds expect for nat 1
        effect_tracker.end_of_turn(test_bugbear)
        assert not is_affected_by(test_goblin, Conditions.PARALYZED)
        assert not is_affected_by(test_bugbear, Conditions.PARALYZED)
        assert test_draconic_sorcerer_5lvl.concentration_effect is None
        assert twinned_hold_person not in effect_tracker.effects
    except Exception as e:
        assert False, f"Raised an exception {e}"