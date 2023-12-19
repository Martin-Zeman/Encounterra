import logging
from abc import abstractmethod, ABC
from enum import Enum, auto

from .actions.action_types import Action, BonusAction, Reaction, Movement, HasteAction
from .battle_map import Map
from .conditions import Conditions, is_affected_by

logger = logging.getLogger("Encounterra")


class ResourceRefreshType(Enum):
    LONG_REST = auto()
    SHORT_REST = auto()
    ROUND = auto()


class Resource(ABC):

    def __init__(self, refresh_type):
        self.refresh_type = refresh_type

    @abstractmethod
    def has_resource(self, **kwargs):
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


class Uses(Resource):
    def __init__(self, uses, refresh_type=ResourceRefreshType.LONG_REST):
        Resource.__init__(self, refresh_type)
        self.curr_uses = uses
        self.max_uses = uses

    def has_resource(self, **kwargs):
        return self.curr_uses > 0

    def use_resource(self, **kwargs):
        self.curr_uses -= 1

    def reset(self):
        self.curr_uses = self.max_uses

    def export_resource(self):
        return self.curr_uses

    def import_resource(self, **kwargs):
        try:
            self.curr_uses = kwargs["uses"]
        except KeyError:
            logger.error("Invalid Uses import resource!")


def use_resources(combatant, action):
    # try:
    #     subject = combatant if combatant.current_wildshape_form is None else combatant.current_wildshape_form
    # except AttributeError:
    subject = combatant
    try:
        action_type = action.factory.action_type
    except AttributeError:
        # TODO revisit this
        # This is here because during construction of FSMs we pass the action_type directly instead of the action instance
        action_type = action
    if isinstance(action_type, Action):
        subject.has_action = False
        match action_type:
            case Action.MELEE_ATTACK | Action.RANGED_ATTACK | Action.RECKLESS_ATTACK | Action.PRE_SWALLOW_BITE | \
                 Action.BITE_AND_SWALLOW | Action.VAMPIRIC_BITE:
                subject.ammo[action.factory.name] -= 1
                try:
                    subject.attack_fsm.trigger(str(action.factory))
                except AttributeError as e:
                    print("FIXME")
            case Action.GRAPPLE_ATTACK:
                subject.attack_fsm.trigger(str(action.factory))
            case Action.DODGE | Action.DASH | Action.DISENGAGE | Action.FIREBOLT | Action.SHOCKING_GRASP:
                pass  # sufficiently tracked by not having an action anymore
            case Action.FIREBALL:
                action.factory.resource.use_resource(level=3)
                subject.already_cast_leveled_spell_this_turn = True
            case Action.HASTE:
                action.factory.resource.use_resource(level=3)
                subject.already_cast_leveled_spell_this_turn = True
            case Action.TWINNED_HASTE:
                action.factory.resource.use_resource(level=3)
                subject.already_cast_leveled_spell_this_turn = True
                subject.curr_sorcery_points -= 3
            case Action.TWINNED_HOLD_PERSON | Action.TWINNED_RAY_OF_ENFEEBLEMENT:
                action.factory.resource.use_resource(level=2)
                subject.already_cast_leveled_spell_this_turn = True
                subject.curr_sorcery_points -= 2
            case Action.CHAOSBOLT | Action.FAERIE_FIRE | Action.MAGIC_MISSILE | Action.BLESS:
                action.factory.resource.use_resource(level=1)
                subject.already_cast_leveled_spell_this_turn = True
            case Action.SCORCHING_RAY | Action.HOLD_PERSON | Action.SPIKE_GROWTH | Action.RAY_OF_ENFEEBLEMENT:
                action.factory.resource.use_resource(level=2)
                subject.already_cast_leveled_spell_this_turn = True
            case Action.TWINNED_FIREBOLT | Action.TWINNED_SHOCKING_GRASP:
                subject.curr_sorcery_points -= 1
            case Action.WILDSHAPE:
                subject.curr_wildshape_uses -= 1
            case Action.POUNCE | Action.CONSTRICT | Action.BREAK_GRAPPLE:
                pass  # Sufficiently tracked by not having an action anymore
            case Action.FLAMING_SPHERE:
                action.factory.resource.use_resource(level=2)
                subject.already_cast_leveled_spell_this_turn = True
            case _:
                logger.error("use_resources: Unknown action type")
    elif isinstance(action_type, BonusAction):
        subject.has_bonus_action = False
        match action_type:
            case BonusAction.BONUS_MELEE_ATTACK | BonusAction.BONUS_RANGED_ATTACK | BonusAction.PAM_BONUS_ATTACK:
                subject.ammo[action.factory.name] -= 1
            case BonusAction.RAGE | BonusAction.TOTEM_RAGE:
                subject.curr_rage_uses -= 1
            case BonusAction.MISTY_STEP:
                action.factory.resource.use_resource(level=2)
                subject.already_cast_leveled_spell_this_turn = True
            case BonusAction.QUICKENED_CHAOSBOLT | BonusAction.QUICKENED_MAGIC_MISSILE | BonusAction.QUICKENED_FAERIE_FIRE | BonusAction.QUICKENED_BLESS:
                action.factory.resource.use_resource(level=1)
                subject.already_cast_leveled_spell_this_turn = True
                subject.curr_sorcery_points -= 2
            case BonusAction.QUICKENED_SCORCHING_RAY | BonusAction.QUICKENED_FLAMING_SPHERE | BonusAction.QUICKENED_HOLD_PERSON | BonusAction.QUICKENED_SPIKE_GROWTH | BonusAction.QUICKENED_RAY_OF_ENFEEBLEMENT:
                action.factory.resource.use_resource(level=2)
                subject.already_cast_leveled_spell_this_turn = True
                subject.curr_sorcery_points -= 2
            case BonusAction.QUICKENED_HASTE:
                action.factory.resource.use_resource(level=3)
                subject.already_cast_leveled_spell_this_turn = True
                subject.curr_sorcery_points -= 2
            case BonusAction.QUICKENED_FIREBALL:
                action.factory.resource.use_resource(level=3)
                subject.already_cast_leveled_spell_this_turn = True
                subject.curr_sorcery_points -= 2
            case BonusAction.QUICKENED_FIREBOLT | BonusAction.QUICKENED_SHOCKING_GRASP:
                subject.curr_sorcery_points -= 2
            case BonusAction.CUNNING_DISENGAGE | BonusAction.FLAMING_SPHERE_RAM | BonusAction.CUNNING_HIDE | BonusAction.CUNNING_DASH:
                pass  # Sufficiently tracked by not having a bonus action anymore
            case BonusAction.MOON_WILDSHAPE:
                subject.curr_wildshape_uses -= 1
            case _:
                logger.error("Unknown bonus action type")
    elif isinstance(action_type, Reaction):
        subject.has_reaction = False
        match action_type:
            case Reaction.REACTION_ATTACK | Reaction.PRE_SWALLOW_BITE_REACTION | Reaction.UNCANNY_DODGE | Reaction.PARRY:
                pass  # Sufficiently tracked by not having a reaction anymore
            case Reaction.SHIELD:
                action.factory.resource.use_resource(level=1)
            case _:
                logger.error("Unknown reaction type")
    elif isinstance(action_type, Movement):
        match action_type:
            case Movement.STANDARD | Movement.DISENGAGED:
                battle_map = Map.get()
                target_position = battle_map.get_combatant_position(subject) + action.increment  # Position is tracked at the original
                decrement = 1
                if is_affected_by(subject, Conditions.PRONE):
                    decrement += 1
                if battle_map.is_difficult_terrain_at(target_position):
                    decrement += 1
                subject.movement -= decrement
            case Movement.GET_UP_FROM_PRONE:
                subject.movement -= subject.speed / 2
            case _:
                logger.error("Unknown movement type")
    elif isinstance(action_type, HasteAction):
        subject.has_haste_action = False
    # elif isinstance(action_type, FreeAction):
    #     pass  # no resources needed
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

    for bonus_action in combatant.bonus_action_factories:
        match bonus_action[0]:
            case BonusAction.RAGE | BonusAction.TOTEM_RAGE:
                combatant.curr_rage_uses = combatant.max_rage_uses
            case _:
                pass

    if hasattr(combatant, "curr_sorcery_points"):
        combatant.curr_sorcery_points = combatant.max_sorcery_points


