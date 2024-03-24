import logging

import numpy as np

from ..abilities.totem_rage import TotemRageFactory
from ..action_resolver import ActionResolver
from ..actions.action_types import Action, BonusAction
from ..conditions import is_affected_by, Conditions, is_affected_by_any, get_grappler
from ..effects.effect import EffectType
from ..effects.regeneration_effect import RegenerationEffect
from ..logging.custom_logger import CustomLogger
from ..misc import SavingThrow, DamageType
from ..spells.faerie_fire import FaerieFireFactory
from ..spells.hunger_of_hadar import HungerOfHadarFactory
from ..spells.spike_growth import SpikeGrowthFactory
from ..spells.twinned_hold_person import TwinnedHoldPersonFactory
from ..teams import Teams
from ..test.fixtures import test_draconic_sorcerer_5lvl, test_goblin, test_bugbear, test_totem_barbarian, test_stone_giant,\
    test_ogre, test_moon_druid, test_giant_toad, teams, effect_tracker, battle_map, test_dragonclaw_cultist, test_brown_bear,\
    test_dire_wolf, test_assassin_rogue, test_draconic_sorcerer_3lvl, test_giant_constrictor_snake, test_twig_blight, \
    test_bandit_captain, test_sabertoother_tiger, test_berserker, test_evil_mage, test_commoner, test_vampire_spawn
from ..actions.action_selector import get_action


def test_remove_and_apply_condition(battle_map, teams, effect_tracker, test_goblin, test_draconic_sorcerer_5lvl, test_bugbear):
    """
    Tests that conditions are correctly applied and removed
    """
    assert False

def test_remove_and_apply_condition_with_initiator(battle_map, teams, effect_tracker, test_goblin, test_draconic_sorcerer_5lvl, test_bugbear):
    """
    Tests that conditions are correctly applied and removed
    """
    assert False