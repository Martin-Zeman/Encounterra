from .actions.action_types import Action, BonusAction, HasteAction, Movement, Reaction, Passive, FreeAction
from .battle_map import Map
from .combatant_coords import Coords
from .effects.effect import EffectType
from .misc import Size
from .conditions import Conditions, is_affected_by_any, get_grappled, is_affected_by
import logging
import numpy as np
import numba_functions as nf

logger = logging.getLogger("Encounterra")


def check_feasibility(combatant, action):
    battle_map = Map.get()
    battle_map.clear_caches()
    action_type = action.factory.action_type
    if isinstance(action_type, Action) or isinstance(action_type, HasteAction):
        if is_affected_by_any(combatant, Conditions.INCAPACITATED, Conditions.STUNNED, Conditions.PARALYZED):
            return False
        if isinstance(action_type, Action):
            res = combatant.has_action
        else:
            res = combatant.has_haste_action
            if not res:
                return False
        match action_type:
            case Action.FIREBALL:
                res &= action.factory.resource.has_resource(level=3)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.are_valid_coords(action.coord)
                res &= nf.get_cartesian_distance_coords(battle_map.get_combatant_position(combatant).get(), np.array([action.coord], dtype=np.int64)) <= action.factory.range
                return res
            case Action.HUNGER_OF_HADAR:
                res &= action.factory.resource.has_resource(level=3)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.are_valid_coords(action.origin)
                res &= nf.get_cartesian_distance_coords(battle_map.get_combatant_position(combatant).get(), np.array([action.origin], dtype=np.int64)) <= action.factory.range
                return res
            case Action.HASTE:
                res &= action.factory.resource.has_resource(level=3)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= not combatant.concentration_effect
                res &= action.target.is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.target) <= action.factory.range
                res &= battle_map.teams.are_allies(combatant, action.target)
                return res
            case Action.CHAOSBOLT:
                res &= action.factory.resource.has_resource(level=1)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.teams.are_enemies(combatant, action.targets[0])
                res &= action.targets[0].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.targets[0]) <= action.factory.range
                return res
            case Action.SCORCHING_RAY:
                res &= action.factory.resource.has_resource(level=2)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.teams.are_enemies(combatant, action.targets[0])
                res &= battle_map.teams.are_enemies(combatant, action.targets[1])
                res &= battle_map.teams.are_enemies(combatant, action.targets[2])
                res &= action.targets[0].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.targets[0]) <= action.factory.range
                res &= action.targets[1].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.targets[1]) <= action.factory.range
                res &= action.targets[2].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.targets[2]) <= action.factory.range
                return res
            case Action.MAGIC_MISSILE:
                res &= action.factory.resource.has_resource(level=1)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.teams.are_enemies(combatant, action.targets[0])
                res &= battle_map.teams.are_enemies(combatant, action.targets[1])
                res &= battle_map.teams.are_enemies(combatant, action.targets[2])
                res &= action.targets[0].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.targets[0]) <= action.factory.range
                res &= action.targets[1].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.targets[1]) <= action.factory.range
                res &= action.targets[2].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.targets[2]) <= action.factory.range
                return res
            case Action.BLESS:
                res &= action.factory.resource.has_resource(level=1)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= not combatant.concentration_effect
                res &= battle_map.teams.are_allies(combatant, action.combatants[0])
                res &= battle_map.teams.are_allies(combatant, action.combatants[1])
                res &= battle_map.teams.are_allies(combatant, action.combatants[2])
                res &= action.combatants[0].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.combatants[0]) <= action.factory.range
                res &= action.combatants[1].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.combatants[1]) <= action.factory.range
                res &= action.combatants[2].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.combatants[2]) <= action.factory.range
                return res
            case Action.FIREBOLT | Action.SHOCKING_GRASP | Action.RAY_OF_FROST:
                res &= battle_map.teams.are_enemies(combatant, action.target)
                res &= action.target.is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.target) <= action.factory.range
                return res
            case Action.TWINNED_FIREBOLT | Action.TWINNED_SHOCKING_GRASP:
                res &= battle_map.teams.are_enemies(combatant, action.targets[0])
                res &= action.targets[0].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.targets[0]) <= action.factory.range
                res &= battle_map.teams.are_enemies(combatant, action.targets[1])
                res &= action.targets[1].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.targets[1]) <= action.factory.range
                res &= combatant.resources[Passive.METAMAGIC].get_resource() > 0
                return res
            case Action.TWINNED_HASTE:
                res &= action.factory.resource.has_resource(level=3)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= not combatant.concentration_effect
                res &= action.targets[0].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.targets[0]) <= action.factory.range
                res &= action.targets[1].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.targets[1]) <= action.factory.range
                res &= battle_map.teams.are_allies(combatant, action.targets[0])
                res &= battle_map.teams.are_allies(combatant, action.targets[0])
                res &= combatant.resources[Passive.METAMAGIC].get_resource() > 2
                return res
            case Action.MELEE_ATTACK | HasteAction.HASTE_MELEE_ATTACK | Action.VAMPIRIC_BITE | \
                 HasteAction.HASTE_VAMPIRIC_BITE | Action.PARALYZING_MELEE_ATTACK | HasteAction.HASTE_PARALYZING_MELEE_ATTACK:
                res |= not combatant.attack_fsm.is_0() and str(action.factory) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, EffectType.RECKLESS_ATTACK)
                res &= combatant.ammo[action.factory.name].has_resource()
                res &= action.target.is_alive() and battle_map.get_hop_distance_combatants(combatant, action.target) <= action.factory.range
                res &= battle_map.teams.are_enemies(combatant, action.target)
                return res
            case Action.MENACING_MELEE_ATTACK:
                res |= not combatant.attack_fsm.is_0() and str(action.factory) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, EffectType.RECKLESS_ATTACK)
                res &= combatant.ammo[action.factory.name].has_resource()
                res &= action.target.is_alive() and battle_map.get_hop_distance_combatants(combatant, action.target) <= action.factory.range
                res &= battle_map.teams.are_enemies(combatant, action.target)
                res &= combatant.resources[Passive.BATTLE_MASTER_MANEUVERS].has_resource()
                return res
            case Action.MENACING_RANGED_ATTACK:
                res |= not combatant.attack_fsm.is_0() and str(action.factory) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, EffectType.RECKLESS_ATTACK)
                res &= combatant.ammo[action.factory.name].has_resource()
                res &= action.target.is_alive() and battle_map.get_hop_distance_combatants(combatant, action.target) <= action.factory.range
                res &= battle_map.teams.are_enemies(combatant, action.target)
                res &= combatant.resources[Passive.BATTLE_MASTER_MANEUVERS].has_resource()
                return res
            case Action.SHAKE_ALLY_AWAKE:
                res &= is_affected_by(action.target, Conditions.CAN_BE_SHAKEN_AWAKE)
                res &= action.target.is_alive() and battle_map.get_hop_distance_combatants(combatant, action.target) <= 1
                res &= battle_map.teams.are_allies(combatant, action.target)
                return res
            case Action.GRAPPLE_ATTACK | HasteAction.HASTE_GRAPPLE_ATTACK:
                res |= not combatant.attack_fsm.is_0() and str(action.factory) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, EffectType.RECKLESS_ATTACK)
                res &= action.target.is_alive() and battle_map.get_hop_distance_combatants(combatant, action.target) <= action.factory.range
                res &= battle_map.teams.are_enemies(combatant, action.target)
                return res
            case Action.RANGED_ATTACK | HasteAction.HASTE_RANGED_ATTACK:
                res |= not combatant.attack_fsm.is_0() and str(action.factory) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, EffectType.RECKLESS_ATTACK)
                res &= combatant.ammo[action.factory.name].has_resource()
                res &= action.target.is_alive() and battle_map.get_hop_distance_combatants(combatant, action.target) <= action.factory.range
                res &= battle_map.teams.are_enemies(combatant, action.target)
                return res
            case Action.RECKLESS_ATTACK:
                res |= not combatant.attack_fsm.is_0() and str(action.factory) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= combatant.ammo[action.factory.name].has_resource()
                res &= action.target.is_alive() and battle_map.get_hop_distance_combatants(combatant, action.target) <= action.factory.range
                res &= battle_map.teams.are_enemies(combatant, action.target)
                return res
            case Action.DASH | HasteAction.HASTE_DASH:
                # Technically, those actions are possible but make no sense
                return res and not is_affected_by_any(combatant, Conditions.GRAPPLED, Conditions.RESTRAINED)
            case Action.DISENGAGE | HasteAction.HASTE_DISENGAGE:
                return res and not is_affected_by_any(combatant, Conditions.GRAPPLED, Conditions.RESTRAINED) and not combatant.has_disengaged
            case Action.DODGE | Action.POUNCE:
                return res
            case Action.BREAK_GRAPPLE:
                return res and is_affected_by_any(combatant, Conditions.GRAPPLED)
            case Action.CONSTRICT:
                return res and (action.target is combatant.constricted_target) if combatant.constricted_target else True
            case Action.WILDSHAPE:
                return res and combatant.resources[Action.WILDSHAPE].has_resource()
            case Action.PRE_SWALLOW_BITE:
                res |= not combatant.attack_fsm.is_0() and str(action.factory) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, EffectType.RECKLESS_ATTACK)
                res &= combatant.ammo[action.factory.name].has_resource()
                res &= action.target.is_alive() and battle_map.get_hop_distance_combatants(combatant, action.target) <= action.factory.range
                res &= battle_map.teams.are_enemies(combatant, action.target)
                res &= (action.target is combatant.constricted_target) if combatant.constricted_target else True
                return res
            case Action.BITE_AND_SWALLOW:
                res |= not combatant.attack_fsm.is_0() and str(action.factory) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, EffectType.RECKLESS_ATTACK)
                res &= combatant.ammo[action.factory.name].has_resource()
                res &= action.target.is_alive() and battle_map.get_hop_distance_combatants(combatant, action.target) <= action.factory.range
                res &= battle_map.teams.are_enemies(combatant, action.target)
                res &= not combatant.swallowed_target
                grappled_target = get_grappled(combatant)
                res &= grappled_target and grappled_target is action.target
                return res
            case Action.FLAMING_SPHERE:
                res &= action.factory.resource.has_resource(level=2)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= not combatant.concentration_effect
                res &= battle_map.are_valid_coords(np.array([action.origin], dtype=np.int64))
                res &= nf.get_cartesian_distance_coords(battle_map.get_combatant_position(combatant).get(), np.array([action.origin], dtype=np.int64)) <= action.factory.range
                return res
            case HasteAction.HASTE_BITE_AND_SWALLOW:
                res |= not combatant.attack_fsm.is_0() and str(action.factory) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, EffectType.RECKLESS_ATTACK)
                res &= combatant.ammo[action.factory.name].has_resource()
                res &= action.target.is_alive() and battle_map.get_hop_distance_combatants(combatant, action.target) <= action.factory.range
                res &= battle_map.teams.are_enemies(combatant, action.target)
                res &= not combatant.swallowed_target
                grappled_target = get_grappled(combatant)
                res &= grappled_target and grappled_target is action.target
                return res
            case HasteAction.HASTE_PRE_SWALLOW_BITE:
                res |= not combatant.attack_fsm.is_0() and str(action.factory) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, EffectType.RECKLESS_ATTACK)
                res &= combatant.ammo[action.factory.name].has_resource()
                res &= action.target.is_alive() and battle_map.get_hop_distance_combatants(combatant, action.target) <= action.factory.range
                res &= battle_map.teams.are_enemies(combatant, action.target)
                res &= (action.target is combatant.constricted_target) if combatant.constricted_target else True
                return res
            case Action.HOLD_PERSON | Action.RAY_OF_ENFEEBLEMENT:
                res &= action.factory.resource.has_resource(level=2)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= not combatant.concentration_effect
                res &= action.combatants[0].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.combatants[0]) <= action.factory.range
                res &= battle_map.teams.are_enemies(combatant, action.combatants[0])
                return res
            case Action.TWINNED_HOLD_PERSON | Action.TWINNED_RAY_OF_ENFEEBLEMENT:
                res &= action.factory.resource.has_resource(level=2)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= combatant.resources[Passive.METAMAGIC].get_resource() > 1
                res &= not combatant.concentration_effect
                res &= action.combatants[0].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.combatants[0]) <= action.factory.range
                res &= action.combatants[1].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.combatants[1]) <= action.factory.range
                res &= battle_map.teams.are_enemies(combatant, action.combatants[0])
                res &= battle_map.teams.are_enemies(combatant, action.combatants[1])
                return res
            case Action.SPIKE_GROWTH:
                res &= action.factory.resource.has_resource(level=2)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= not combatant.concentration_effect
                res &= battle_map.are_valid_coords(np.array([action.origin], dtype=np.int64))
                res &= nf.get_cartesian_distance_coords(battle_map.get_combatant_position(combatant).get(), np.array([action.origin], dtype=np.int64)) <= action.factory.range
                return res
            case Action.SLEEP:
                res &= action.factory.resource.has_resource(level=1)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= not combatant.concentration_effect
                res &= battle_map.are_valid_coords(np.array([action.origin], dtype=np.int64))
                res &= nf.get_cartesian_distance_coords(battle_map.get_combatant_position(combatant).get(), np.array([action.origin], dtype=np.int64)) <= action.factory.range
                return res
            case Action.FAERIE_FIRE:
                res &= action.factory.resource.has_resource(level=1)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= not combatant.concentration_effect
                res &= battle_map.are_valid_coords(np.array([action.origin], dtype=np.int64))
                res &= nf.get_cartesian_distance_coords(battle_map.get_combatant_position(combatant).get(), action.get_affected_coords()) <= action.factory.range
                return res
            case Action.THUNDERWAVE:
                res &= action.factory.resource.has_resource(level=1)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.are_valid_coords(np.array([action.coord], dtype=np.int64))
                res &= nf.get_cartesian_distance_coords(battle_map.get_combatant_position(combatant).get(),
                                                                action.get_affected_coords()) <= action.factory.range
                return res
            case Action.LAY_ON_HANDS:
                res &= combatant.resources[Action.LAY_ON_HANDS].get_resource() >= action.hp_amount
                res &= action.target.is_alive() and battle_map.get_hop_distance_combatants(combatant, action.target) <= 1
                res &= battle_map.teams.are_allies(combatant, action.target)
                return res
            case Action.CURE_WOUNDS:
                res &= action.factory.resource.has_resource(level=1)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= action.target.is_alive() and battle_map.get_hop_distance_combatants(combatant, action.target) <= action.factory.range
                res &= battle_map.teams.are_allies(combatant, action.target)
                return res
            case Action.CONIC_BREATH_WEAPON:
                res &= combatant.resources[Action.CONIC_BREATH_WEAPON].has_resource()
                res &= (nf.get_hop_distance_coords(battle_map.get_combatant_position(combatant).get(), np.array([action.coord], dtype=np.int64)) == 0)
                return res
            case Action.CONIC_BREATH_WEAPON_ATTACK:
                res |= not combatant.attack_fsm.is_0() and str(action.factory) in combatant.attack_fsm.get_available_transitions()
                res &= combatant.resources[Action.CONIC_BREATH_WEAPON_ATTACK].has_resource()
                res &= (nf.get_hop_distance_coords(battle_map.get_combatant_position(combatant).get(), np.array([action.coord], dtype=np.int64)) == 0)
                return res
            case Action.LINE_BREATH_WEAPON:
                res &= combatant.resources[Action.LINE_BREATH_WEAPON].has_resource()
                res &= (nf.get_hop_distance_coords(battle_map.get_combatant_position(combatant).get(), np.array([action.coord], dtype=np.int64)) == 0)
                return res
            case _:
                logger.error(f"check_feasibility: Unknown action type {action_type}")
                return False
    elif isinstance(action_type, BonusAction):
        if is_affected_by_any(combatant, Conditions.INCAPACITATED, Conditions.STUNNED, Conditions.PARALYZED):
            return False
        res = combatant.has_bonus_action
        match action_type:
            case BonusAction.PAM_BONUS_ATTACK:
                res &= action.target.is_alive() and battle_map.get_hop_distance_combatants(combatant, action.target) <= action.range
                res &= battle_map.teams.are_enemies(combatant, action.target)
                return res
            case BonusAction.RAGE:
                return res and combatant.resources[BonusAction.RAGE].has_resource() and not battle_map.effect_tracker.is_affecting_combatant(combatant, EffectType.RAGE)
            case BonusAction.TOTEM_RAGE:
                return res and combatant.resources[BonusAction.TOTEM_RAGE].has_resource() and not battle_map.effect_tracker.is_affecting_combatant(combatant, EffectType.TOTEM_RAGE)
            case BonusAction.MISTY_STEP:
                res &= action.factory.resource.has_resource(level=2)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= nf.get_cartesian_distance_coords(battle_map.get_combatant_position(combatant).get(), np.array([action.coord], dtype=np.int64)) <= action.factory.range
                res &= battle_map.are_valid_coords(action.coord) and battle_map.are_empty_or_self(Coords(action.coord, combatant.size.value), combatant)
                return res
            case BonusAction.QUICKENED_CHAOSBOLT:
                res &= action.factory.resource.has_resource(level=1)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= action.targets[0].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.targets[0]) <= action.factory.range
                res &= combatant.resources[Passive.METAMAGIC].get_resource() > 1
                res &= battle_map.teams.are_enemies(combatant, action.targets[0])
                return res
            case Action.MAGIC_MISSILE:
                res &= action.factory.resource.has_resource(level=1)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.teams.are_enemies(combatant, action.targets[0])
                res &= battle_map.teams.are_enemies(combatant, action.targets[1])
                res &= battle_map.teams.are_enemies(combatant, action.targets[2])
                res &= action.targets[0].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.targets[0]) <= action.factory.range
                res &= action.targets[1].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.targets[1]) <= action.factory.range
                res &= action.targets[2].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.targets[2]) <= action.factory.range
                return res
            case BonusAction.QUICKENED_SCORCHING_RAY:
                res &= action.factory.resource.has_resource(level=2)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= action.targets[0].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.targets[0]) <= action.factory.range
                res &= action.targets[1].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.targets[1]) <= action.factory.range
                res &= action.targets[2].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.targets[2]) <= action.factory.range
                res &= combatant.resources[Passive.METAMAGIC].get_resource() > 1
                res &= battle_map.teams.are_enemies(combatant, action.targets[0])
                res &= battle_map.teams.are_enemies(combatant, action.targets[1])
                res &= battle_map.teams.are_enemies(combatant, action.targets[2])
                return res
            case BonusAction.QUICKENED_BLESS:
                res &= action.factory.resource.has_resource(level=1)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= not combatant.concentration_effect
                res &= battle_map.teams.are_allies(combatant, action.combatants[0])
                res &= battle_map.teams.are_allies(combatant, action.combatants[1])
                res &= battle_map.teams.are_allies(combatant, action.combatants[2])
                res &= action.combatants[0].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.combatants[0]) <= action.factory.range
                res &= action.combatants[1].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.combatants[1]) <= action.factory.range
                res &= action.combatants[2].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.combatants[2]) <= action.factory.range
                return res
            case BonusAction.QUICKENED_HASTE:
                res &= action.factory.resource.has_resource(level=3)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.get_cartesian_distance_combatants(combatant, action.target) <= action.factory.range
                res &= combatant.resources[Passive.METAMAGIC].get_resource() > 1
                res &= battle_map.teams.are_allies(combatant, action.target)
                return res
            case BonusAction.QUICKENED_HOLD_PERSON:
                res &= action.factory.resource.has_resource(level=2)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= not combatant.concentration_effect
                res &= action.combatants[0].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.combatants[0]) <= action.factory.range
                res &= battle_map.teams.are_enemies(combatant, action.combatants[0])
                return res
            case BonusAction.QUICKENED_SPIKE_GROWTH:
                res &= action.factory.resource.has_resource(level=2)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= not combatant.concentration_effect
                res &= battle_map.are_valid_coords(np.array([action.origin]))
                res &= nf.get_cartesian_distance_coords(battle_map.get_combatant_position(combatant).get(), np.array([action.origin])) <= action.factory.range
                return res
            case BonusAction.QUICKENED_SLEEP:
                res &= action.factory.resource.has_resource(level=1)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= not combatant.concentration_effect
                res &= battle_map.are_valid_coords(np.array([action.origin]))
                res &= nf.get_cartesian_distance_coords(battle_map.get_combatant_position(combatant).get(), np.array([action.origin])) <= action.factory.range
                return res
            case BonusAction.QUICKENED_FAERIE_FIRE:
                res &= action.factory.resource.has_resource(level=1)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= not combatant.concentration_effect
                res &= battle_map.are_valid_coords(np.array([action.origin]))
                res &= nf.get_cartesian_distance_coords(battle_map.get_combatant_position(combatant).get(), action.get_affected_coords()) <= action.factory.range
                return res
            case BonusAction.QUICKENED_THUNDERWAVE:
                res &= action.factory.resource.has_resource(level=1)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= battle_map.are_valid_coords(np.array([action.coord]))
                res &= nf.get_cartesian_distance_coords(battle_map.get_combatant_position(combatant).get(), action.get_affected_coords()) <= action.factory.range
                return res
            case BonusAction.QUICKENED_FIREBALL:
                res &= action.factory.resource.has_resource(level=3)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= nf.get_cartesian_distance_coords(battle_map.get_combatant_position(combatant).get(), np.array([action.coord])) <= action.factory.range
                res &= combatant.resources[Passive.METAMAGIC].get_resource() > 1
                res &= battle_map.are_valid_coords(action.coord)
                return res
            case BonusAction.QUICKENED_HUNGER_OF_HADAR:
                res &= action.factory.resource.has_resource(level=3)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= nf.get_cartesian_distance_coords(battle_map.get_combatant_position(combatant).get(), np.array([action.origin])) <= action.factory.range
                res &= combatant.resources[Passive.METAMAGIC].get_resource() > 1
                res &= battle_map.are_valid_coords(action.origin)
                return res
            case BonusAction.QUICKENED_FIREBOLT | BonusAction.QUICKENED_SHOCKING_GRASP | BonusAction.QUICKENED_RAY_OF_FROST:
                res &= action.target.is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.target) <= action.factory.range
                res &= combatant.resources[Passive.METAMAGIC].get_resource() > 1
                res &= battle_map.teams.are_enemies(combatant, action.target)
                return res
                # TODO check sorcery points, checks if the spell even has casting time of an action, check if leveled spell has already been cast
            case BonusAction.CUNNING_HIDE | BonusAction.CUNNING_DASH | BonusAction.SHILLELAGH | BonusAction.AGGRESSIVE:
                return res
            case BonusAction.CUNNING_DISENGAGE:
                return res and not combatant.has_disengaged
            case BonusAction.MOON_WILDSHAPE:
                return res and combatant.resources[Action.WILDSHAPE].has_resource()
            case BonusAction.FLAMING_SPHERE_RAM:
                return res  # TODO add more conditions
            case BonusAction.SECOND_WIND:
                return res and combatant.resources[BonusAction.SECOND_WIND].has_resource()
            case BonusAction.HEALING_WORD:
                res &= action.factory.resource.has_resource(level=1)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= action.target.is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.target) <= action.factory.range
                res &= battle_map.teams.are_allies(combatant, action.target)
                return res
            case BonusAction.TWINNED_HEALING_WORD:
                res &= action.factory.resource.has_resource(level=1)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= combatant.resources[Passive.METAMAGIC].get_resource() > 0
                res &= action.targets[0].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.targets[0]) <= action.factory.range
                res &= action.targets[1].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.targets[1]) <= action.factory.range
                res &= battle_map.teams.are_allies(combatant, action.targets[0])
                res &= battle_map.teams.are_allies(combatant, action.targets[1])
                return res
            case BonusAction.SHIELD_OF_FAITH:
                res &= action.factory.resource.has_resource(level=1)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= not combatant.concentration_effect
                res &= action.combatants[0].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.combatants[0]) <= action.factory.range
                res &= battle_map.teams.are_allies(combatant, action.combatants[0])
                return res
            case BonusAction.VOW_OF_ENMITY:
                res &= combatant.resources[Passive.CHANNEL_DIVINITY].has_resource()
                res &= action.combatants[0].is_alive() and battle_map.get_cartesian_distance_combatants(combatant, action.combatants[0]) <= 2
                res &= battle_map.teams.are_enemies(combatant, action.combatants[0])
                return res
            case _:
                logger.error("Unknown bonus action")
                return False
    elif isinstance(action_type, Reaction):
        if is_affected_by_any(combatant, Conditions.INCAPACITATED, Conditions.STUNNED, Conditions.PARALYZED):
            return False
        match action_type:
            case Reaction.SHIELD:
                return combatant.has_reaction and action.factory.resource.has_resource(level=1)
            case Reaction.REACTION_ATTACK | Reaction.UNCANNY_DODGE | Reaction.PARRY | Reaction.REACTION_PARALYZING_MELEE_ATTACK:
                return combatant.has_reaction
            case Reaction.PRE_SWALLOW_BITE_REACTION:
                return combatant.has_reaction and not combatant.constricted_target
            case Reaction.RIPOSTE:
                return combatant.has_reaction and combatant.resources[Passive.BATTLE_MASTER_MANEUVERS].has_resource()
            case _:
                logger.error("Unknown reaction")
        return combatant.has_reaction
    elif isinstance(action_type, Movement):
        if is_affected_by_any(combatant, Conditions.INCAPACITATED, Conditions.STUNNED, Conditions.PARALYZED):
            return False
        match action_type:
            case Movement.STANDARD | Movement.DISENGAGED:
                target_position = battle_map.get_combatant_position(combatant) + np.array(action.increment, dtype=np.int64)
                movement_needed = 1 if not battle_map.is_difficult_terrain_at(target_position) else 2
                res = combatant.movement >= movement_needed and battle_map.are_valid_coords(target_position.get()) and battle_map.are_empty_or_self(target_position, combatant)
                res &= not is_affected_by_any(combatant, Conditions.GRAPPLED, Conditions.RESTRAINED)
                return res
            case Movement.GET_UP_FROM_PRONE:
                return combatant.movement >= (combatant.speed / 2)
            case _:
                logger.error("Unknown movement")
    elif isinstance(action_type, FreeAction):
        match action_type:
            case FreeAction.ACTION_SURGE:
                return combatant.resources[FreeAction.ACTION_SURGE].has_resource()
            case _:
                logger.error("Unknown free action")
    # elif isinstance(action_type, FreeAction):
    #     match action_type:
    #         case _:
    #             logger.error("Unknown free action")
    #             return False
    else:
        logger.error(f"check_feasibility: Unknown action type {action_type}")
        return False


def check_feasibility_light(combatant, action):
    """
    Checks feasibility in terms of resources and combat rules. Doesn't check arguments of actions.
    :param combatant: initiator of the action
    :param action: action to be considered in form of a tuple (action_type, action_factory)
    :return: True if feasible, false otherwise
    """
    battle_map = Map.get()
    action_type = action[0]
    if isinstance(action_type, Action) or isinstance(action_type, HasteAction):
        # if is_affected_by_any(combatant, Conditions.INCAPACITATED, Conditions.STUNNED, Conditions.PARALYZED):
        #     return False
        if isinstance(action_type, Action):
            res = combatant.has_action
        else:
            res = combatant.has_haste_action
            if not res:
                return False
        match action_type:
            case Action.FIREBALL | Action.HUNGER_OF_HADAR:
                res &= action[1].resource.has_resource(level=3)
                res &= not combatant.already_cast_leveled_spell_this_turn
                return res
            case Action.HASTE:
                res &= action[1].resource.has_resource(level=3)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= not combatant.concentration_effect
                # res &= (len(battle_map.teams.get_allies(combatant)) > 0)
                return res
            case Action.CHAOSBOLT | Action.MAGIC_MISSILE | Action.THUNDERWAVE:
                res &= action[1].resource.has_resource(level=1)
                res &= not combatant.already_cast_leveled_spell_this_turn
                return res
            case Action.FAERIE_FIRE | Action.BLESS | Action.SLEEP:
                res &= action[1].resource.has_resource(level=1)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= not combatant.concentration_effect
                return res
            case Action.SCORCHING_RAY:
                res &= action[1].resource.has_resource(level=2)
                res &= not combatant.already_cast_leveled_spell_this_turn
                return res
            case Action.HOLD_PERSON | Action.SPIKE_GROWTH | Action.RAY_OF_ENFEEBLEMENT:
                res &= action[1].resource.has_resource(level=2)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= not combatant.concentration_effect
                return res
            case Action.TWINNED_HOLD_PERSON | Action.TWINNED_RAY_OF_ENFEEBLEMENT:
                res &= action[1].resource.has_resource(level=2)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= combatant.resources[Passive.METAMAGIC].get_resource() > 1
                res &= not combatant.concentration_effect
                return res
            case Action.FIREBOLT | Action.SHOCKING_GRASP | Action.DODGE | Action.POUNCE | Action.CONSTRICT | Action.SHAKE_ALLY_AWAKE | Action.RAY_OF_FROST:
                return res
            case Action.TWINNED_FIREBOLT | Action.TWINNED_SHOCKING_GRASP:
                return res and combatant.resources[Passive.METAMAGIC].get_resource() > 0
            case Action.TWINNED_HASTE:
                res &= action[1].resource.has_resource(level=3)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= not combatant.concentration_effect
                res &= combatant.resources[Passive.METAMAGIC].get_resource() > 2
                res &= (len(battle_map.teams.get_allies(combatant)) > 0)
                return res
            case Action.MELEE_ATTACK | Action.RANGED_ATTACK | HasteAction.HASTE_MELEE_ATTACK | \
                 HasteAction.HASTE_RANGED_ATTACK | Action.VAMPIRIC_BITE | HasteAction.HASTE_VAMPIRIC_BITE | \
                 Action.PARALYZING_MELEE_ATTACK | HasteAction.HASTE_PARALYZING_MELEE_ATTACK:
                res |= not combatant.attack_fsm.is_0() and str(action[1]) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, EffectType.RECKLESS_ATTACK)
                res &= combatant.ammo[action[1].name].has_resource()
                return res
            case Action.MENACING_MELEE_ATTACK | Action.MENACING_RANGED_ATTACK:
                res |= not combatant.attack_fsm.is_0() and str(action[1]) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, EffectType.RECKLESS_ATTACK)
                res &= combatant.ammo[action[1].name].has_resource()
                res &= combatant.resources[Passive.BATTLE_MASTER_MANEUVERS].has_resource()
                return res
            case Action.GRAPPLE_ATTACK | HasteAction.HASTE_GRAPPLE_ATTACK:  # No ammo for this type
                res |= not combatant.attack_fsm.is_0() and str(action[1]) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, EffectType.RECKLESS_ATTACK)
                return res
            case Action.RECKLESS_ATTACK:
                res |= not combatant.attack_fsm.is_0() and str(action[1]) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= combatant.ammo[action[1].name].has_resource()
                return res
            case Action.DASH | HasteAction.HASTE_DASH:
                return res and not is_affected_by_any(combatant, Conditions.GRAPPLED, Conditions.RESTRAINED)
            case Action.DISENGAGE | HasteAction.HASTE_DISENGAGE:
                return res and not is_affected_by_any(combatant, Conditions.GRAPPLED, Conditions.RESTRAINED) and not combatant.has_disengaged  # Don't want to disengage twice
            case Action.WILDSHAPE:
                return res and combatant.resources[Action.WILDSHAPE].has_resource()
            case Action.PRE_SWALLOW_BITE:
                res |= not combatant.attack_fsm.is_0() and str(action[1]) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, EffectType.RECKLESS_ATTACK)
                res &= combatant.ammo[action[1].name].has_resource()
                return res
            case Action.BITE_AND_SWALLOW:
                res |= not combatant.attack_fsm.is_0() and str(action[1]) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, EffectType.RECKLESS_ATTACK)
                res &= combatant.ammo[action[1].name].has_resource()
                res &= not combatant.swallowed_target
                grappled_target = get_grappled(combatant)
                res &= grappled_target is not None and grappled_target.size.value <= Size.MEDIUM.value
                return res
            case Action.FLAMING_SPHERE:
                res &= action[1].resource.has_resource(level=2)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= not combatant.concentration_effect
                return res
            case Action.LAY_ON_HANDS:
                res &= combatant.resources[Action.LAY_ON_HANDS].has_resource()
                return res
            case Action.CURE_WOUNDS:
                res &= action[1].resource.has_resource(level=1)
                res &= not combatant.already_cast_leveled_spell_this_turn
                return res
            case Action.CONIC_BREATH_WEAPON:
                res &= combatant.resources[Action.CONIC_BREATH_WEAPON].has_resource()
                return res
            case Action.CONIC_BREATH_WEAPON_ATTACK:
                res |= not combatant.attack_fsm.is_0() and str(action[1]) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= combatant.resources[Action.CONIC_BREATH_WEAPON_ATTACK].has_resource()
                return res
            case Action.LINE_BREATH_WEAPON:
                res &= combatant.resources[Action.LINE_BREATH_WEAPON].has_resource()
                return res
            case HasteAction.HASTE_BITE_AND_SWALLOW:
                res |= not combatant.attack_fsm.is_0() and str(action[1]) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, EffectType.RECKLESS_ATTACK)
                res &= combatant.ammo[action[1].name].has_resource()
                res &= not combatant.swallowed_target
                grappled_target = get_grappled(combatant)
                res &= grappled_target is not None and grappled_target.size.value <= Size.MEDIUM.value
                return res
            case HasteAction.HASTE_PRE_SWALLOW_BITE:
                res |= not combatant.attack_fsm.is_0() and str(action[1]) in combatant.attack_fsm.get_available_transitions()  # TODO I think the is_0 can be omitted
                res &= not battle_map.effect_tracker.is_affecting_combatant(combatant, EffectType.RECKLESS_ATTACK)
                res &= combatant.ammo[action[1].name].has_resource()
                return res
            case _:
                logger.error(f"check_feasibility_light: Unknown action type {action_type}")
                return False
    elif isinstance(action_type, BonusAction):
        # if is_affected_by_any(combatant, Conditions.INCAPACITATED, Conditions.STUNNED, Conditions.PARALYZED):
        #     return False
        res = combatant.has_bonus_action
        match action_type:
            case BonusAction.PAM_BONUS_ATTACK:  # TODO Remove this
                return res
            case BonusAction.RAGE:
                return res and combatant.resources[BonusAction.RAGE].has_resource() and not battle_map.effect_tracker.is_affecting_combatant(combatant, EffectType.RAGE)
            case BonusAction.TOTEM_RAGE:
                return res and combatant.resources[BonusAction.TOTEM_RAGE].has_resource() and not battle_map.effect_tracker.is_affecting_combatant(combatant, EffectType.TOTEM_RAGE)
            case BonusAction.MISTY_STEP:
                res &= action[1].resource.has_resource(level=2)
                res &= not combatant.already_cast_leveled_spell_this_turn
                return res
            case BonusAction.QUICKENED_CHAOSBOLT | BonusAction.QUICKENED_MAGIC_MISSILE | BonusAction.QUICKENED_THUNDERWAVE:
                res &= action[1].resource.has_resource(level=1)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= combatant.resources[Passive.METAMAGIC].get_resource() > 1
                return res
            case BonusAction.QUICKENED_FAERIE_FIRE | BonusAction.QUICKENED_BLESS | BonusAction.QUICKENED_SLEEP:
                res &= action[1].resource.has_resource(level=1)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= combatant.resources[Passive.METAMAGIC].get_resource() > 1
                res &= not combatant.concentration_effect
                return res
            case BonusAction.QUICKENED_SCORCHING_RAY:
                res &= action[1].resource.has_resource(level=2)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= combatant.resources[Passive.METAMAGIC].get_resource() > 1
                return res
            case BonusAction.QUICKENED_HOLD_PERSON | BonusAction.QUICKENED_SPIKE_GROWTH:
                res &= action[1].resource.has_resource(level=2)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= combatant.resources[Passive.METAMAGIC].get_resource() > 1
                res &= not combatant.concentration_effect
                return res
            case BonusAction.QUICKENED_HASTE:
                res &= action[1].resource.has_resource(level=3)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= not combatant.concentration_effect
                res &= combatant.resources[Passive.METAMAGIC].get_resource() > 1
                return res
            case BonusAction.QUICKENED_FIREBALL | BonusAction.QUICKENED_HUNGER_OF_HADAR:
                res &= action[1].resource.has_resource(level=3)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= combatant.resources[Passive.METAMAGIC].get_resource() > 1
                return res
            case BonusAction.QUICKENED_FIREBOLT | BonusAction.QUICKENED_SHOCKING_GRASP | BonusAction.QUICKENED_RAY_OF_FROST:
                return res and combatant.resources[Passive.METAMAGIC].get_resource() > 1
                # TODO check sorcery points, checks if the spell even has casting time of an action, check if leveled spell has already been cast
            case BonusAction.CUNNING_DISENGAGE:
                return res and not combatant.has_disengaged  # Don't want to disengage twice
            case BonusAction.FLAMING_SPHERE_RAM | BonusAction.CUNNING_HIDE | BonusAction.CUNNING_DASH | BonusAction.SHILLELAGH | BonusAction.AGGRESSIVE:
                return res
            case BonusAction.MOON_WILDSHAPE:
                return res and combatant.resources[Action.WILDSHAPE].has_resource()
            case BonusAction.SECOND_WIND:
                return res and combatant.resources[BonusAction.SECOND_WIND].has_resource()
            case BonusAction.HEALING_WORD:
                res &= action[1].resource.has_resource(level=1)
                res &= not combatant.already_cast_leveled_spell_this_turn
                return res
            case BonusAction.TWINNED_HEALING_WORD:
                res &= action[1].resource.has_resource(level=1)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= combatant.resources[Passive.METAMAGIC].get_resource() > 0
                res &= (len(battle_map.teams.get_allies(combatant)) > 0)
                return res
            case BonusAction.SHIELD_OF_FAITH:
                res &= action[1].resource.has_resource(level=1)
                res &= not combatant.already_cast_leveled_spell_this_turn
                res &= not combatant.concentration_effect
                return res
            case BonusAction.VOW_OF_ENMITY:
                return res and combatant.resources[Passive.CHANNEL_DIVINITY].has_resource()
            case _:
                logger.error("Unknown bonus action")
                return False
    elif isinstance(action_type, Reaction):
        if is_affected_by_any(combatant, Conditions.INCAPACITATED):
            return False
        match action_type:
            case Reaction.SHIELD:
                return combatant.has_reaction and action[1].resource.has_resource(level=1)
            case Reaction.UNCANNY_DODGE:
                return combatant.has_reaction
            case Reaction.RIPOSTE:  # TODO Does it need to be here?
                return combatant.has_reaction and combatant.resources[Passive.BATTLE_MASTER_MANEUVERS].has_resource()
            case _:
                logger.error("Unknown reaction")
        return combatant.has_reaction
    elif isinstance(action_type, Movement):
        return combatant.movement > 0 and not is_affected_by_any(combatant,
            Conditions.GRAPPLED,
            Conditions.RESTRAINED)
    elif isinstance(action_type, FreeAction):
        match action_type:
            case FreeAction.ACTION_SURGE:
                return combatant.resources[FreeAction.ACTION_SURGE].has_resource()
            case _:
                logger.error("Unknown free action")
    else:
        logger.error(f"check_feasibility_light: Unknown action type {action_type}")
        return False


def get_feasible_factories(actions, combatant):
    return [a for a in actions if check_feasibility_light(combatant, a)]
