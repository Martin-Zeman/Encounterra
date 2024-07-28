import logging

import numpy as np

from simulator.abilities.totem_rage import TotemRageFactory
from simulator.action_resolver import ActionResolver
from simulator.actions.action_types import Action, BonusAction
from simulator.conditions import is_affected_by, Conditions, is_affected_by_any, get_grappler, Condition, apply_condition, \
    find_condition_index, remove_condition
from simulator.effects.effect import EffectType
from simulator.effects.regeneration_effect import RegenerationEffect
from simulator.logging.custom_logger import CustomLogger
from simulator.misc import SavingThrow, DamageType
from simulator.spells.faerie_fire import FaerieFireFactory
from simulator.spells.hunger_of_hadar import HungerOfHadarFactory
from simulator.spells.spike_growth import SpikeGrowthFactory
from simulator.spells.twinned_hold_person import TwinnedHoldPersonFactory
from simulator.teams import Teams
from simulator.test.fixtures import test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, test_totem_barbarian, test_stone_giant,\
    test_ogre, test_moon_druid_lvl_5, test_giant_toad, teams, effect_tracker, battle_map, test_dragonclaw_cultist, test_brown_bear,\
    test_dire_wolf, test_assassin_rogue, test_draconic_sorcerer_3lvl, test_giant_constrictor_snake, test_twig_blight, \
    test_bandit_captain, test_sabertoother_tiger, test_berserker, test_evil_mage, test_commoner, test_vampire_spawn
from simulator.actions.action_selector import get_action


def test_remove_and_apply_condition(battle_map, teams, effect_tracker, test_goblin, test_draconic_sorcerer_5lvl, test_bugbear):
    """
    Tests that conditions are correctly applied and removed
    """
    apply_condition(test_goblin, Condition(Conditions.PARALYZED, test_draconic_sorcerer_5lvl))
    index = find_condition_index(test_goblin.conditions, Conditions.PARALYZED)
    assert index is not None
    assert is_affected_by(test_goblin, Conditions.PARALYZED)
    index = find_condition_index(test_goblin.conditions, Conditions.PARALYZED, test_draconic_sorcerer_5lvl)  # specify the initiator
    assert index is not None
    index = find_condition_index(test_goblin.conditions, Conditions.PARALYZED, test_bugbear)  # specify an initiator but the wrong one
    assert index is None
    remove_condition(test_goblin, Conditions.PARALYZED, test_bugbear)  # won't remove anything
    index = find_condition_index(test_goblin.conditions, Conditions.PARALYZED)
    assert index is not None
    assert is_affected_by(test_goblin, Conditions.PARALYZED)
    index = find_condition_index(test_goblin.conditions, Conditions.PARALYZED, test_draconic_sorcerer_5lvl)  # specify the initiator
    assert index is not None

    remove_condition(test_goblin, Conditions.PARALYZED)  # will remove
    index = find_condition_index(test_goblin.conditions, Conditions.PARALYZED)
    assert index is None
    assert not is_affected_by(test_goblin, Conditions.PARALYZED)
    index = find_condition_index(test_goblin.conditions, Conditions.PARALYZED, test_draconic_sorcerer_5lvl)  # specify the initiator
    assert index is None

    apply_condition(test_goblin, Condition(Conditions.PARALYZED, test_draconic_sorcerer_5lvl))  # Apply again

    index = find_condition_index(test_goblin.conditions, Conditions.PARALYZED)
    assert index is not None
    assert is_affected_by(test_goblin, Conditions.PARALYZED)
    index = find_condition_index(test_goblin.conditions, Conditions.PARALYZED, test_draconic_sorcerer_5lvl)  # specify the initiator
    assert index is not None
    index = find_condition_index(test_goblin.conditions, Conditions.PARALYZED, test_bugbear)  # specify an initiator but the wrong one
    assert index is None

    remove_condition(test_goblin, Conditions.PARALYZED, test_draconic_sorcerer_5lvl)  # will also remove
    index = find_condition_index(test_goblin.conditions, Conditions.PARALYZED)
    assert index is None
    assert not is_affected_by(test_goblin, Conditions.PARALYZED)
    index = find_condition_index(test_goblin.conditions, Conditions.PARALYZED, test_draconic_sorcerer_5lvl)  # specify the initiator
    assert index is None
