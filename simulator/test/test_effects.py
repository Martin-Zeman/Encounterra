import logging

import numpy as np
import pytest

from simulator.abilities.totem_rage import TotemRageFactory
from simulator.action_resolver import ActionResolver
from simulator.actions.action_types import Action
from simulator.conditions import is_affected_by, Conditions, is_affected_by_any, get_grappler
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
    test_ogre, test_moon_druid, test_giant_toad, teams, effect_tracker, battle_map, test_dragonclaw_cultist, test_brown_bear,\
    test_dire_wolf, test_assassin_rogue, test_draconic_sorcerer_3lvl, test_giant_constrictor_snake, test_twig_blight, \
    test_bandit_captain, test_sabertoother_tiger, test_berserker, test_evil_mage, test_commoner, test_vampire_spawn
from simulator.actions.action_selector import get_action


@pytest.mark.flaky(reruns=3)
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


@pytest.mark.flaky(reruns=3)
def test_limited_duration_effect_non_self_target(battle_map, teams, effect_tracker, test_goblin, test_moon_druid, test_bugbear, test_ogre):
    """
    Tests that effects with a limited duration really expire post their duration. The focus is on the type of effect
    where the target(s) and the initiator are not one and the same.
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_goblin, test_moon_druid, test_bugbear, test_ogre]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    teams.add_combatant_to_team(test_moon_druid, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.RED)
    teams.add_combatant_to_team(test_ogre, Teams.Color.RED)
    battle_map.set_combatant_coordinates(test_goblin, np.array([3, 5]))
    battle_map.set_combatant_coordinates(test_moon_druid, np.array([8, 5]))
    battle_map.set_combatant_coordinates(test_bugbear, np.array([4, 5]))
    battle_map.set_combatant_coordinates(test_ogre, np.array([3, 6]))

    battle_map.build_adjacency_matrix()
    test_goblin.saving_throws[SavingThrow.DEX] = -20  # Making sure it fails expect for nat 20
    test_bugbear.saving_throws[SavingThrow.DEX] = -20  # Making sure it fails expect for nat 20
    test_ogre.saving_throws[SavingThrow.DEX] = -20  # Making sure it fails expect for nat 20

    faerie_fire_factory = FaerieFireFactory(15, Action.FAERIE_FIRE, test_moon_druid, test_moon_druid.spellslots)
    faerie_fire = faerie_fire_factory.create(np.array([3, 5]))

    try:
        action_resolver.resolve_action(faerie_fire, test_moon_druid)

        for idx in range(10):
            assert effect_tracker.is_affecting_combatant(test_goblin, EffectType.FAERIE_FIRE)
            assert effect_tracker.is_affecting_combatant(test_bugbear, EffectType.FAERIE_FIRE)
            assert effect_tracker.is_affecting_combatant(test_ogre, EffectType.FAERIE_FIRE)
            assert test_moon_druid.concentration_effect is faerie_fire
            effect_tracker.start_of_turn_tick(test_moon_druid)

        assert not effect_tracker.is_affecting_combatant(test_goblin, EffectType.FAERIE_FIRE)
        assert not effect_tracker.is_affecting_combatant(test_bugbear, EffectType.FAERIE_FIRE)
        assert not effect_tracker.is_affecting_combatant(test_ogre, EffectType.FAERIE_FIRE)
        assert test_moon_druid.concentration_effect is None
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_limited_duration_effect_self_target(battle_map, teams, effect_tracker, test_goblin, test_totem_barbarian):
    """
    Tests that effects with a limited duration really expire post their duration. The focus is on the type of effect
    where the target(s) and the initiator are one and the same.
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_goblin, test_totem_barbarian]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_goblin, Teams.Color.RED)
    teams.add_combatant_to_team(test_totem_barbarian, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(test_goblin, np.array([3, 5]))
    battle_map.set_combatant_coordinates(test_totem_barbarian, np.array([8, 5]))

    battle_map.build_adjacency_matrix()

    totem_rage_factory = TotemRageFactory(test_totem_barbarian)
    totem_rage = totem_rage_factory.create(test_totem_barbarian)

    try:
        action_resolver.resolve_action(totem_rage, test_totem_barbarian)

        for idx in range(10):
            assert effect_tracker.is_affecting_combatant(test_totem_barbarian, EffectType.TOTEM_RAGE)
            effect_tracker.start_of_turn_tick(test_totem_barbarian)
        assert not effect_tracker.is_affecting_combatant(test_totem_barbarian, EffectType.TOTEM_RAGE)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_spheric_aoe_effects(battle_map, teams, effect_tracker, test_draconic_sorcerer_5lvl, test_goblin, test_ogre, test_bugbear, test_commoner, test_dire_wolf):
    """
    Tests that effects with a limited duration really expire post their duration. The focus is on the type of effect
    where the target(s) and the initiator are one and the same.
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_draconic_sorcerer_5lvl, test_goblin, test_ogre, test_bugbear]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_draconic_sorcerer_5lvl, Teams.Color.RED)
    teams.add_combatant_to_team(test_goblin, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_ogre, Teams.Color.BLUE)
    teams.add_combatant_to_team(test_bugbear, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(test_draconic_sorcerer_5lvl, np.array([3, 5]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([8, 5]))  # Fully insude
    battle_map.set_combatant_coordinates(test_ogre, np.array([8, 6]))  # Fully inside
    battle_map.set_combatant_coordinates(test_bugbear, np.array([9, 5]))  # Fully inside
    battle_map.set_combatant_coordinates(test_commoner, np.array([7, 9]))  # Outside
    battle_map.set_combatant_coordinates(test_dire_wolf, np.array([5, 1]))  # Touching just with a corner

    battle_map.build_adjacency_matrix()

    hunger_of_hadar_factory = HungerOfHadarFactory(15, Action.HUNGER_OF_HADAR, test_draconic_sorcerer_5lvl, test_draconic_sorcerer_5lvl.spellslots)
    hunger_of_hadar = hunger_of_hadar_factory.create(np.array([8, 5]))

    spike_growth_factory = SpikeGrowthFactory(Action.SPIKE_GROWTH, test_draconic_sorcerer_5lvl, test_draconic_sorcerer_5lvl.spellslots)
    spike_growth = spike_growth_factory.create(np.array([8, 5]))

    try:
        action_resolver.resolve_action(hunger_of_hadar, test_draconic_sorcerer_5lvl)
        assert effect_tracker.is_affecting_combatant(test_goblin, EffectType.HUNGER_OF_HADAR)
        assert effect_tracker.is_affecting_combatant(test_ogre, EffectType.HUNGER_OF_HADAR)
        assert effect_tracker.is_affecting_combatant(test_bugbear, EffectType.HUNGER_OF_HADAR)
        assert not effect_tracker.is_affecting_combatant(test_commoner, EffectType.HUNGER_OF_HADAR)
        assert effect_tracker.is_affecting_combatant(test_dire_wolf, EffectType.HUNGER_OF_HADAR)
        assert not effect_tracker.is_affecting_combatant(test_draconic_sorcerer_5lvl, EffectType.HUNGER_OF_HADAR)

        test_draconic_sorcerer_5lvl.concentration_effect = None
        test_draconic_sorcerer_5lvl.new_turn()
        action_resolver.resolve_action(spike_growth, test_draconic_sorcerer_5lvl)
        assert effect_tracker.is_affecting_combatant(test_goblin, EffectType.SPIKE_GROWTH)
        assert effect_tracker.is_affecting_combatant(test_ogre, EffectType.SPIKE_GROWTH)
        assert effect_tracker.is_affecting_combatant(test_bugbear, EffectType.SPIKE_GROWTH)
        assert not effect_tracker.is_affecting_combatant(test_commoner, EffectType.SPIKE_GROWTH)
        assert effect_tracker.is_affecting_combatant(test_dire_wolf, EffectType.SPIKE_GROWTH)
        assert not effect_tracker.is_affecting_combatant(test_draconic_sorcerer_5lvl, EffectType.SPIKE_GROWTH)
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_start_of_turn_digestion_effect(battle_map, teams, effect_tracker, test_giant_toad, test_goblin):
    """
    Tests that a combatant is properly discarded if died as a result of a digestion effect. Also that the digestion
    effect is properly removed.
    """
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_giant_toad, test_goblin]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_giant_toad, Teams.Color.RED)
    teams.add_combatant_to_team(test_goblin, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(test_giant_toad, np.array([3, 5]))
    battle_map.set_combatant_coordinates(test_goblin, np.array([5, 5]))

    battle_map.build_adjacency_matrix()

    test_giant_toad.bite[1].on_hit[0].dc = 20
    test_giant_toad.bite[1].to_hit = 20
    test_goblin.athletics = 1  # Making sure the goblin is grappled
    test_goblin.ac = 1  # Making sure the goblin is grappled
    test_goblin.curr_hp = 1000  # Making sure the goblin survives
    bite = test_giant_toad.bite[1].create(test_goblin)

    try:
        action_resolver.resolve_action(bite, test_giant_toad)
        assert is_affected_by_any(test_goblin, Conditions.GRAPPLED)
        assert get_grappler(test_goblin) is test_giant_toad
        assert not effect_tracker.is_affecting_combatant(test_goblin, EffectType.DIGESTION)
        test_giant_toad.new_turn()
        bite_and_swallow = test_giant_toad.bite_and_swallow[1].create(test_goblin)
        action_resolver.resolve_action(bite_and_swallow, test_giant_toad)
        assert effect_tracker.effects
        assert effect_tracker.is_affecting_combatant(test_goblin, EffectType.DIGESTION)
        test_goblin.curr_hp = 1  # Making sure digestion kills it
        effect_tracker.start_of_turn(test_goblin)
        assert not effect_tracker.is_affecting_combatant(test_goblin, EffectType.DIGESTION)
        assert not effect_tracker.effects
        assert not test_goblin.is_alive()
    except Exception as e:
        assert False, f"Raised an exception {e}"


def test_start_of_turn_regeneration_effect(battle_map, teams, effect_tracker, test_vampire_spawn, test_ogre):
    CustomLogger(logging.WARNING)
    battle_map.set_effect_tracker(effect_tracker)
    combatants = [test_vampire_spawn, test_ogre]
    action_resolver = ActionResolver(combatants, teams, effect_tracker)
    teams.add_combatant_to_team(test_vampire_spawn, Teams.Color.RED)
    teams.add_combatant_to_team(test_ogre, Teams.Color.BLUE)
    battle_map.set_combatant_coordinates(test_vampire_spawn, np.array([3, 5]))
    battle_map.set_combatant_coordinates(test_ogre, np.array([4, 5]))

    battle_map.build_adjacency_matrix()

    test_ogre.greatclub_attack[1].dmg_bonus = 30
    test_ogre.greatclub_attack[1].to_hit = 20
    greatclub_attack = test_ogre.greatclub_attack[1].create(test_vampire_spawn)
    test_vampire_spawn.ac = 1  # Making sure the goblin is grappled
    test_vampire_spawn.curr_hp = 5  # Making sure the goblin survives
    effect_tracker.add(RegenerationEffect(test_vampire_spawn, 10, DamageType.Radiant))

    try:
        effect_tracker.start_of_turn(test_vampire_spawn)
        assert test_vampire_spawn.curr_hp == 15
        assert effect_tracker.effects
        assert effect_tracker.is_affecting_combatant(test_vampire_spawn, EffectType.REGENERATION)
        action_resolver.resolve_action(greatclub_attack, test_ogre)
        assert not test_vampire_spawn.is_alive()
        effect_tracker.start_of_turn(test_vampire_spawn)
        assert not effect_tracker.effects
        assert not effect_tracker.is_affecting_combatant(test_vampire_spawn, EffectType.REGENERATION)
    except Exception as e:
        assert False, f"Raised an exception {e}"
