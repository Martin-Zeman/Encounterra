from enum import Enum, auto

from simulator.abilities.pounce import PounceFactory
from simulator.abilities.rage import RageFactory
from simulator.abilities.reckless_attack import RecklessAttackFactory
from simulator.abilities.totem_rage import TotemRageFactory
from simulator.abilities.wildshape import WildshapeFactory
from simulator.actions.disengage import DisengageFactory
from simulator.actions.dodge import DodgeFactory
from simulator.actions.melee_attack import MeleeAttackFactory
from simulator.actions.ranged_attack import RangedAttackFactory
from simulator.spells.chaosbolt import ChaosboltFactory
from simulator.spells.fireball import FireballFactory
from simulator.spells.firebolt import FireboltFactory
from simulator.spells.haste import HasteFactory
from simulator.spells.misty_step import MistyStepFactory
from simulator.spells.scorching_ray import ScorchingRayFactory
from simulator.spells.shield import ShieldFactory
from simulator.spells.twinned_firebolt import TwinnedFireboltFactory
from simulator.spells.twinned_haste import TwinnedHasteFactory


class Action(Enum):
    MELEE_ATTACK = auto()
    RANGED_ATTACK = auto()
    RECKLESS_ATTACK = auto()
    DODGE = auto()
    DASH = auto()
    DISENGAGE = auto()
    FIREBALL = auto()
    FIREBOLT = auto()
    CHAOSBOLT = auto()
    HASTE = auto()
    HUNGER_OF_HADAR = auto()
    SPIKE_GROWTH = auto()
    CLOUD_OF_DAGGERS = auto()
    HIDE = auto()
    TWINNED_FIREBOLT = auto()
    TWINNED_HASTE = auto()
    SCORCHING_RAY = auto()
    FAERIE_FIRE = auto()
    WILDSHAPE = auto()
    POUNCE = auto()
    CONSTRICT = auto()


class BonusAction(Enum):
    BONUS_MELEE_ATTACK = auto()
    BONUS_RANGED_ATTACK = auto()
    PAM_BONUS_ATTACK = auto()
    RAGE = auto()
    TOTEM_RAGE = auto()
    MISTY_STEP = auto()
    CUNNING_DODGE = auto()
    CUNNING_DISENGAGE = auto()
    CUNNING_HIDE = auto()
    QUICKENED_FIREBALL = auto()
    QUICKENED_FIREBOLT = auto()
    QUICKENED_CHAOSBOLT = auto()
    QUICKENED_HASTE = auto()
    QUICKENED_HUNGER_OF_HADAR = auto()
    QUICKENED_SPIKE_GROWTH = auto()
    QUICKENED_CLOUD_OF_DAGGERS = auto()
    QUICKENED_SCORCHING_RAY = auto()
    QUICKENED_FAERIE_FIRE = auto()
    MOON_WILDSHAPE = auto()


class Reaction(Enum):
    REACTION_ATTACK = auto()
    SHIELD = auto()


class Movement(Enum):
    STANDARD = auto()
    DISENGAGE = auto()
    CUNNING_DISENGAGE = auto()
    FORCED = auto()
    GET_UP_FROM_PRONE = auto()


class HasteAction(Enum):
    HASTE_MELEE_ATTACK = auto()
    HASTE_RANGED_ATTACK = auto()
    HASTE_DASH = auto()
    HASTE_DISENGAGE = auto()
    HASTE_HIDE = auto()


class Passive(Enum):
    MULTIATTACK = auto()
    SENTINEL = auto()
    POLEARM_MASTER = auto()
    DANGER_SENSE = auto()
    METAMAGIC = auto()
    PACK_TACTICS = auto()


class MetaAction(Enum):
    DONE = auto()
    QUICKENED_SPELL = auto()
    TWINNED_SPELL = auto()
    EMPOWERED_SPELL = auto()


PRIORITY_ACTIONS = {
    Action.DODGE: ("Dodge", "do_"),
    Action.DISENGAGE: ("Disengage", "di_"),
    BonusAction.CUNNING_DODGE: ("Cunning Dodge", "do_"),
    BonusAction.CUNNING_DISENGAGE: ("Cunning Disengage", "di_"),
    BonusAction.TOTEM_RAGE: ("TotemRage", "m_"),
    BonusAction.RAGE: ("Rage", "m_"),
    HasteAction.HASTE_DISENGAGE: ("Disengage", "di_")
}

TO_FACTORY = {
    Action.MELEE_ATTACK: MeleeAttackFactory,
    Action.RANGED_ATTACK: RangedAttackFactory,
    Action.RECKLESS_ATTACK: RecklessAttackFactory,
    Action.DODGE: DodgeFactory,
    Action.DASH: None,
    Action.DISENGAGE: DisengageFactory,
    Action.FIREBALL: FireballFactory,
    Action.FIREBOLT: FireboltFactory,
    Action.CHAOSBOLT: ChaosboltFactory,
    Action.HASTE: HasteFactory,
    Action.HIDE: None,
    Action.TWINNED_FIREBOLT: TwinnedFireboltFactory,
    Action.TWINNED_HASTE: TwinnedHasteFactory,
    Action.SCORCHING_RAY: ScorchingRayFactory,
    Action.WILDSHAPE: WildshapeFactory,
    Action.POUNCE: PounceFactory,

    BonusAction.BONUS_MELEE_ATTACK: MeleeAttackFactory,
    BonusAction.BONUS_RANGED_ATTACK: RangedAttackFactory,
    BonusAction.PAM_BONUS_ATTACK: MeleeAttackFactory,
    BonusAction.RAGE: RageFactory,
    BonusAction.TOTEM_RAGE: TotemRageFactory,
    BonusAction.MISTY_STEP: MistyStepFactory,
    BonusAction.CUNNING_DODGE: DodgeFactory,
    BonusAction.CUNNING_DISENGAGE: DisengageFactory,
    BonusAction.CUNNING_HIDE: None,
    BonusAction.QUICKENED_FIREBALL: FireballFactory,
    BonusAction.QUICKENED_FIREBOLT: FireboltFactory,
    BonusAction.QUICKENED_CHAOSBOLT: ChaosboltFactory,
    BonusAction.QUICKENED_HASTE: HasteFactory,
    BonusAction.QUICKENED_SCORCHING_RAY: ScorchingRayFactory,
    BonusAction.MOON_WILDSHAPE: WildshapeFactory,

    Reaction.SHIELD: ShieldFactory,
    Reaction.REACTION_ATTACK: MeleeAttackFactory,

    HasteAction.HASTE_MELEE_ATTACK: MeleeAttackFactory,
    HasteAction.HASTE_RANGED_ATTACK: RangedAttackFactory,
    HasteAction.HASTE_DISENGAGE: DisengageFactory,
    HasteAction.HASTE_HIDE: None,
    HasteAction.HASTE_DASH: None
}
TO_QUICKENED = {
    Action.FIREBALL: BonusAction.QUICKENED_FIREBALL,
    Action.FIREBOLT: BonusAction.QUICKENED_FIREBOLT,
    Action.CHAOSBOLT: BonusAction.QUICKENED_CHAOSBOLT,
    Action.HASTE: BonusAction.QUICKENED_HASTE,
    Action.SCORCHING_RAY: BonusAction.QUICKENED_SCORCHING_RAY
}
TO_TWINNED = {Action.FIREBOLT: Action.TWINNED_FIREBOLT, Action.HASTE: Action.TWINNED_HASTE}
TO_HASTED = {Action.MELEE_ATTACK: HasteAction.HASTE_MELEE_ATTACK, Action.RANGED_ATTACK: HasteAction.HASTE_RANGED_ATTACK, Action.HIDE: HasteAction.HASTE_HIDE, Action.DASH: HasteAction.HASTE_DASH, Action.DISENGAGE: HasteAction.HASTE_DISENGAGE}