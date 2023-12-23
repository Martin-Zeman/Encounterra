from enum import Flag, auto
from typing import Union

from .effects.effect import Effect
from .misc import PhaseOfTurn


class Conditions(Flag):
    NONE = auto()
    BLINDED = auto()
    CHARMED = auto()
    DEAFENED = auto()
    FRIGHTENED = auto()
    GRAPPLED = auto()
    INCAPACITATED = auto()
    INVISIBLE = auto()
    PARALYZED = auto()
    PETRIFIED = auto()
    POISONED = auto()
    PRONE = auto()
    RESTRAINED = auto()
    STUNNED = auto()
    UNCONSCIOUS = auto()
    SWALLOWED = auto()  # Meta-Condition
    GRAPPLING = auto()  # Meta-Condition
    AWAKENED_BY_DMG = auto()  # Meta-Condition


class Condition:
    def __init__(self, conditions, initiator, effect=None, target=None):
        self.conditions = conditions  # Could be multiples such as grapple + restrained go often together
        self.initiator = initiator
        self.effect = effect
        self.target = target  # If there is a target, e.g. GRAPPLING has a target


# class ConditionWithoutDC(Condition):
#     def __init__(self, conditions, initiator, effect=None, target=None):
#         Condition.__init__(self, conditions, initiator, target)
#         self.effect = effect
#         self.target = target  # If there is a target, e.g. GRAPPLING has a target


class ConditionWithDC(Condition):
    def __init__(self, conditions, st, dc, initiator, phase, effect=None, target=None):
        Condition.__init__(self, conditions, initiator, effect, target)
        self.st = st
        self.dc = dc
        self.phase = phase


def apply_condition(combatant, condition: Condition):
    combatant.is_swallowed = [True, condition.initiator] if Conditions.SWALLOWED in condition.conditions else combatant.is_swallowed # This is an optimization to speed up conditions look-up since it's done frequently
    combatant.conditions.append(condition)


def find_condition_index(condition_list, condition: Conditions, initiator=None) -> Union[int, None]:
    """
    Find the index of a specific condition in the list.

    Parameters:
    - combatant (Combatant): The combatant in question.
    - condition (Conditions): The condition to find.
    - initiator: The initiator of the condition (optional).

    Returns:
    - int: The index of the condition if found, None otherwise.
    """
    for idx, cond in enumerate(condition_list):
        if (not initiator or cond.initiator is initiator) and condition in cond.conditions:
            return idx
    return None


def remove_condition(combatant, condition: Conditions, initiator=None) -> Union[None, Effect]:
    """
    Remove a specific condition from the list.

    Parameters:
    - combatant (Combatant): The combatant in question.
    - condition (Conditions): The condition to remove.
    - initiator: The initiator of the condition (optional).

    Returns:
    - Any: The removed condition if found, None otherwise.
    """
    index = find_condition_index(combatant.conditions, condition, initiator)
    if index is not None:
        removed_condition = combatant.conditions.pop(index)
        combatant.is_swallowed = [False, None] if condition is Conditions.SWALLOWED else combatant.is_swallowed
        return removed_condition
    return None


def remove_all_conditions_of_type(combatant, condition: Conditions):
    """
    Remove all conditions of a specific type from a combatant.

    Parameters:
    - combatant: The combatant from which conditions are to be removed.
    - condition (Conditions): The type of condition to remove.
    """
    combatant.is_swallowed = [False, None] if condition is Conditions.SWALLOWED else combatant.is_swallowed
    combatant.dc_conditions = [dc_cond for dc_cond in combatant.dc_conditions if condition not in dc_cond.conditions]
    combatant.conditions = [cond for cond in combatant.conditions if condition not in cond.conditions]


def is_affected_by(combatant, condition: Conditions):
    for dc_cond in combatant.dc_conditions:
        if condition in dc_cond.conditions:
            return True
    for cond in combatant.conditions:
        if condition in cond.conditions:
            return True
    return condition in combatant.conditions


def get_swallower(combatant):
    return combatant.is_swallowed[1]


def get_grappler(combatant):
    """
    Get the initiator of the grappler condition affecting the combatant.

    Parameters:
    - combatant: The combatant to check.

    Returns:
    - Any: The initiator of the grappler condition, or None if not found.
    """
    for condition_list in (combatant.dc_conditions, combatant.conditions):
        for cond in condition_list:
            if Conditions.GRAPPLED in cond.conditions:
                return cond.initiator
    return None


def get_grappled(combatant):
    """
    Get the target of the grappling condition affecting the combatant.

    Parameters:
    - combatant: The combatant to check.

    Returns:
    - Any: The target of the grappler condition, or None if not found.
    """
    for condition_list in (combatant.dc_conditions, combatant.conditions):
        for cond in condition_list:
            if Conditions.GRAPPLING in cond.conditions:
                return cond.target
    return None


def needs_to_break_out_of_grapple(combatant):
    for dc_cond in combatant.dc_conditions:
        if Conditions.GRAPPLED in dc_cond.conditions and dc_cond.phase == PhaseOfTurn.ACTION:
            return dc_cond
    return None


def break_out_of_grapple(combatant):
    # TODO this is a simplification, there can potentially be multiple grapples by multiple targets
    for idx, dc_cond in enumerate(combatant.dc_conditions):
        if Conditions.GRAPPLED in dc_cond.conditions and dc_cond.phase == PhaseOfTurn.ACTION:
            del combatant.dc_conditions[idx]
            break


def is_affected_by_any(combatant, *args):
    for condition in args:
        for dc_cond in combatant.dc_conditions:
            if condition in dc_cond.conditions:
                return True
        for cond in combatant.conditions:
            if condition in cond.conditions:
                return True
    return False


def apply_dc_condition(combatant, condition: ConditionWithDC):
    combatant.is_swallowed = [True, condition.initiator] if Conditions.SWALLOWED in condition.conditions else combatant.is_swallowed  # This is an optimization to speed up conditions look-up since it's done frequently
    combatant.dc_conditions.append(condition)


def remove_dc_condition(combatant, condition: Conditions, initiator=None) -> Union[None, Effect]:
    """
    Remove a specific dc condition from the combatant.

    Parameters:
    - combatant (Combatant): The combatant in question.
    - condition (Conditions): The condition to remove.
    - initiator: The initiator of the condition (optional).

    Returns:
    - Any: The removed condition if found, None otherwise.
    """
    index = find_condition_index(combatant.dc_conditions, condition, initiator)
    if index is not None:
        removed_condition = combatant.dc_conditions.pop(index)
        combatant.is_swallowed = [False, None] if condition is Conditions.SWALLOWED else combatant.is_swallowed
        return removed_condition
    return None
