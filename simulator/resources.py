import logging
import math
from abc import abstractmethod, ABC
from enum import Enum, auto

from .actions.action_types import Action, BonusAction, Reaction, Movement, HasteAction, Passive, FreeAction
from .battle_map import Map
from .conditions import Conditions, is_affected_by

logger = logging.getLogger("Encounterra")


class ResourceDepletionLevel(Enum):
    FULLY_RESTED = 1
    PARTIALLY_DEPLETED = 2
    FULLY_DEPLETED = 3


class ResourceRefreshType(Enum):
    LONG_REST = auto()
    SHORT_REST = auto()
    ROUND = auto()
    NEVER = auto()


class Resource(ABC):

    def __init__(self, refresh_type: ResourceRefreshType):
        self.refresh_type = refresh_type

    @abstractmethod
    def has_resource(self, **kwargs):
        pass

    @abstractmethod
    def get_resource(self, **kwargs):
        pass

    @abstractmethod
    def use_resource(self, **kwargs):
        pass

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def export_resource(self):
        pass

    @abstractmethod
    def import_resource(self, **kwargs):
        pass

    @abstractmethod
    def deplete_resource(self, level: ResourceDepletionLevel):
        pass


class Uses(Resource):
    def __init__(self, uses, refresh_type=ResourceRefreshType.LONG_REST):
        Resource.__init__(self, refresh_type)
        self.curr_uses = uses
        self.max_uses = uses

    def has_resource(self, **kwargs):
        return self.curr_uses > 0

    def get_resource(self, **kwargs):
        return self.curr_uses

    def use_resource(self, uses=1, **kwargs):
        self.curr_uses -= uses

    def add_resource(self, uses=1):
        self.curr_uses += uses

    def set_resource(self, uses):
        self.curr_uses = uses

    def is_inf(self):
        return self.curr_uses == math.inf

    def reset(self):
        self.curr_uses = self.max_uses

    def export_resource(self):
        return self.curr_uses

    def import_resource(self, **kwargs):
        try:
            self.curr_uses = kwargs["uses"]
        except KeyError:
            logger.error("Invalid Uses import resource!")

    def deplete_resource(self, level: ResourceDepletionLevel):
        match level:
            case ResourceDepletionLevel.FULLY_DEPLETED:
                self.curr_uses = 0
            case ResourceDepletionLevel.PARTIALLY_DEPLETED:
                self.curr_uses = self.max_uses // 2
            case _:
                pass


def use_resources(combatant, action, **kwargs):
    try:
        action_type = action.factory.action_type
    except AttributeError:
        # TODO revisit this
        # This is here because during construction of FSMs and in the case of PRECISION attacks we pass the action_type directly instead of the action instance
        action_type = action
    if isinstance(action_type, Action):
        combatant.has_action = False
        match action_type:
            case Action.MELEE_ATTACK | Action.RANGED_ATTACK | Action.RECKLESS_ATTACK | Action.PRE_SWALLOW_BITE | \
                 Action.BITE_AND_SWALLOW | Action.VAMPIRIC_BITE:
                combatant.ammo[action.factory.name].use_resource()
                combatant.attack_fsm.trigger(str(action.factory))
            case Action.MENACING_MELEE_ATTACK | Action.MENACING_RANGED_ATTACK:# | Action.PRECISION_MELEE_ATTACK | Action.PRECISION_RANGED_ATTACK:
                combatant.ammo[action.factory.name].use_resource()
                combatant.attack_fsm.trigger(str(action.factory))
                combatant.resources[Passive.BATTLE_MASTER_MANEUVERS].use_resource()
            case Action.PRECISION_ATTACK:
                combatant.resources[Passive.BATTLE_MASTER_MANEUVERS].use_resource()
            case Action.GRAPPLE_ATTACK:
                combatant.attack_fsm.trigger(str(action.factory))
            case Action.DODGE | Action.DASH | Action.DISENGAGE | Action.FIREBOLT | Action.SHOCKING_GRASP | Action.SHAKE_ALLY_AWAKE:
                pass  # sufficiently tracked by not having an action anymore
            case Action.FIREBALL | Action.HASTE | Action.HUNGER_OF_HADAR:
                action.factory.resource.use_resource(level=3)
                combatant.already_cast_leveled_spell_this_turn = True
            case Action.TWINNED_HASTE:
                action.factory.resource.use_resource(level=3)
                combatant.already_cast_leveled_spell_this_turn = True
                combatant.resources[Passive.METAMAGIC].use_resource(3)
            case Action.TWINNED_HOLD_PERSON | Action.TWINNED_RAY_OF_ENFEEBLEMENT:
                action.factory.resource.use_resource(level=2)
                combatant.already_cast_leveled_spell_this_turn = True
                combatant.resources[Passive.METAMAGIC].use_resource(2)
            case Action.CHAOSBOLT | Action.FAERIE_FIRE | Action.MAGIC_MISSILE | Action.BLESS | Action.SLEEP | Action.THUNDERWAVE | Action.CURE_WOUNDS:
                action.factory.resource.use_resource(level=1)
                combatant.already_cast_leveled_spell_this_turn = True
            case Action.SCORCHING_RAY | Action.HOLD_PERSON | Action.SPIKE_GROWTH | Action.RAY_OF_ENFEEBLEMENT | Action.FLAMING_SPHERE:
                action.factory.resource.use_resource(level=2)
                combatant.already_cast_leveled_spell_this_turn = True
            case Action.TWINNED_FIREBOLT | Action.TWINNED_SHOCKING_GRASP:
                combatant.resources[Passive.METAMAGIC].use_resource()
            case Action.WILDSHAPE:
                combatant.resources[Action.WILDSHAPE].use_resource()
            case Action.POUNCE | Action.CONSTRICT | Action.BREAK_GRAPPLE | Action.NOP:  # TODO NOP probably not needed
                pass  # Sufficiently tracked by not having an action anymore
            case Action.LAY_ON_HANDS:
                combatant.resources[Action.LAY_ON_HANDS].use_resource(action.hp_amount)
            case _:
                logger.error(f"use_resources: Unknown action type {action_type}")
    elif isinstance(action_type, BonusAction):
        combatant.has_bonus_action = False
        match action_type:
            case BonusAction.BONUS_MELEE_ATTACK | BonusAction.BONUS_RANGED_ATTACK | BonusAction.PAM_BONUS_ATTACK:
                combatant.ammo[action.factory.name].use_resource()
            case BonusAction.BONUS_MENACING_MELEE_ATTACK | BonusAction.BONUS_MENACING_RANGED_ATTACK:# | BonusAction.BONUS_PRECISION_MELEE_ATTACK | BonusAction.BONUS_PRECISION_RANGED_ATTACK:
                combatant.ammo[action.factory.name].use_resource()
                combatant.resources[Passive.BATTLE_MASTER_MANEUVERS].use_resource()
            case BonusAction.RAGE | BonusAction.TOTEM_RAGE:
                combatant.resources[action_type].use_resource()
            case BonusAction.MISTY_STEP:
                action.factory.resource.use_resource(level=2)
                combatant.already_cast_leveled_spell_this_turn = True
            case BonusAction.QUICKENED_CHAOSBOLT | BonusAction.QUICKENED_MAGIC_MISSILE | BonusAction.QUICKENED_FAERIE_FIRE | BonusAction.QUICKENED_BLESS | BonusAction.QUICKENED_SLEEP | BonusAction.QUICKENED_THUNDERWAVE:
                action.factory.resource.use_resource(level=1)
                combatant.already_cast_leveled_spell_this_turn = True
                combatant.resources[Passive.METAMAGIC].use_resource(2)
            case BonusAction.QUICKENED_SCORCHING_RAY | BonusAction.QUICKENED_FLAMING_SPHERE | BonusAction.QUICKENED_HOLD_PERSON | BonusAction.QUICKENED_SPIKE_GROWTH | BonusAction.QUICKENED_RAY_OF_ENFEEBLEMENT:
                action.factory.resource.use_resource(level=2)
                combatant.already_cast_leveled_spell_this_turn = True
                combatant.resources[Passive.METAMAGIC].use_resource(2)
            case BonusAction.QUICKENED_FIREBALL | BonusAction.QUICKENED_HASTE | BonusAction.QUICKENED_HUNGER_OF_HADAR:
                action.factory.resource.use_resource(level=3)
                combatant.already_cast_leveled_spell_this_turn = True
                combatant.resources[Passive.METAMAGIC].use_resource(2)
            case BonusAction.QUICKENED_FIREBOLT | BonusAction.QUICKENED_SHOCKING_GRASP:
                combatant.resources[Passive.METAMAGIC].use_resource(2)
            case BonusAction.CUNNING_DISENGAGE | BonusAction.FLAMING_SPHERE_RAM | BonusAction.CUNNING_HIDE | BonusAction.CUNNING_DASH | BonusAction.SHILLELAGH | BonusAction.NOP:  # TODO NOP probably not needed
                pass  # Sufficiently tracked by not having a bonus action anymore
            case BonusAction.MOON_WILDSHAPE:
                combatant.resources[Action.WILDSHAPE].use_resource()
            case BonusAction.SECOND_WIND:
                combatant.resources[BonusAction.SECOND_WIND].use_resource()
            case BonusAction.HEALING_WORD | BonusAction.SHIELD_OF_FAITH:
                action.factory.resource.use_resource(level=1)
                combatant.already_cast_leveled_spell_this_turn = True
            case BonusAction.TWINNED_HEALING_WORD:
                action.factory.resource.use_resource(level=1)
                combatant.already_cast_leveled_spell_this_turn = True
                combatant.resources[Passive.METAMAGIC].use_resource(1)
            case _:
                logger.error("Unknown bonus action type")
    elif isinstance(action_type, Reaction):
        combatant.has_reaction = False
        match action_type:
            case Reaction.REACTION_ATTACK | Reaction.PRE_SWALLOW_BITE_REACTION | Reaction.UNCANNY_DODGE | Reaction.PARRY:
                pass  # Sufficiently tracked by not having a reaction anymore
            case Reaction.SHIELD:
                action.factory.resource.use_resource(level=1)
            case Reaction.RIPOSTE:
                combatant.resources[Passive.BATTLE_MASTER_MANEUVERS].use_resource()
            case _:
                logger.error("Unknown reaction type")
    elif isinstance(action_type, Movement):
        match action_type:
            case Movement.STANDARD | Movement.DISENGAGED:
                battle_map = Map.get()
                target_position = battle_map.get_combatant_position(combatant) + action.increment  # Position is tracked at the original
                decrement = 1
                if is_affected_by(combatant, Conditions.PRONE):
                    decrement += 1
                if battle_map.is_difficult_terrain_at(target_position):
                    decrement += 1
                combatant.movement -= decrement
            case Movement.GET_UP_FROM_PRONE:
                combatant.movement -= combatant.speed / 2
            case _:
                logger.error("Unknown movement type")
    elif isinstance(action_type, HasteAction):
        combatant.has_haste_action = False
    elif isinstance(action_type, FreeAction):
        match action_type:
            case FreeAction.ACTION_SURGE:
                combatant.resources[FreeAction.ACTION_SURGE].use_resource()
            case _:
                logger.error("Unknown free action type")
        pass  # no resources needed
    else:
        logger.error("Unknown high level action class")


def reset_resources(combatant):
    """
    First resets those resources that are common for all combatants which are reset by the Combatant parent class. Then it resets all the
    dynamically added resources
    :param combatant:
    :return: void
    """
    combatant.reset()
    # Currently no dynamic resources for actions
    # for action in combatant.actions:
    #     pass

    # if hasattr(combatant, "curr_sorcery_points"):
    #     combatant.curr_sorcery_points = combatant.max_sorcery_points


