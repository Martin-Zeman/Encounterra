import logging
from enum import auto, Enum

from simulator.abilities.bite_and_swallow import BiteAndSwallowFactory
from simulator.abilities.pre_swallow_bite import PreSwallowBiteFactory
from simulator.abilities.constrict import ConstrictFactory
from simulator.abilities.pounce import PounceFactory
from simulator.abilities.rage import RageFactory
from simulator.abilities.reckless_attack import RecklessAttackFactory
from simulator.abilities.totem_rage import TotemRageFactory
from simulator.abilities.wildshape import WildshapeFactory
from simulator.actions.action_types import Action, BonusAction, HasteAction, Reaction
from simulator.actions.disengage import DisengageFactory
from simulator.actions.dodge import DodgeFactory
from simulator.actions.melee_attack import MeleeAttackFactory
from simulator.actions.ranged_attack import RangedAttackFactory
from simulator.spells.chaosbolt import ChaosboltFactory
from simulator.spells.fireball import FireballFactory
from simulator.spells.firebolt import FireboltFactory
from simulator.spells.flaming_sphere import FlamingSphereFactory
from simulator.spells.haste import HasteFactory
from simulator.spells.hold_person import HoldPersonFactory
from simulator.spells.twinned_hold_person import TwinnedHoldPersonFactory
from simulator.spells.misty_step import MistyStepFactory
from simulator.spells.scorching_ray import ScorchingRayFactory
from simulator.spells.shield import ShieldFactory
from simulator.spells.twinned_firebolt import TwinnedFireboltFactory
from simulator.spells.twinned_haste import TwinnedHasteFactory

logger = logging.getLogger("EncounTroll")

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
    Action.CONSTRICT: ConstrictFactory,
    Action.PRE_SWALLOW_BITE: PreSwallowBiteFactory,
    Action.BITE_AND_SWALLOW: BiteAndSwallowFactory,
    Action.FLAMING_SPHERE: FlamingSphereFactory,
    Action.HOLD_PERSON: HoldPersonFactory,
    Action.TWINNED_HOLD_PERSON: TwinnedHoldPersonFactory,

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
    BonusAction.QUICKENED_HOLD_PERSON: HoldPersonFactory,

    Reaction.SHIELD: ShieldFactory,
    Reaction.REACTION_ATTACK: MeleeAttackFactory,
    Reaction.PRE_SWALLOW_BITE_REACTION: PreSwallowBiteFactory,

    HasteAction.HASTE_MELEE_ATTACK: MeleeAttackFactory,
    HasteAction.HASTE_PRE_SWALLOW_BITE: PreSwallowBiteFactory,
    HasteAction.HASTE_BITE_AND_SWALLOW: BiteAndSwallowFactory,
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
    Action.SCORCHING_RAY: BonusAction.QUICKENED_SCORCHING_RAY,
    Action.HOLD_PERSON: BonusAction.QUICKENED_HOLD_PERSON
}
TO_TWINNED = {Action.FIREBOLT: Action.TWINNED_FIREBOLT, Action.HASTE: Action.TWINNED_HASTE, Action.HOLD_PERSON: Action.TWINNED_HOLD_PERSON}
TO_HASTED = {Action.MELEE_ATTACK: HasteAction.HASTE_MELEE_ATTACK, Action.RANGED_ATTACK: HasteAction.HASTE_RANGED_ATTACK, \
             Action.HIDE: HasteAction.HASTE_HIDE, Action.DASH: HasteAction.HASTE_DASH, Action.DISENGAGE: HasteAction.HASTE_DISENGAGE,\
             Action.BITE_AND_SWALLOW: HasteAction.HASTE_BITE_AND_SWALLOW, Action.PRE_SWALLOW_BITE: HasteAction.HASTE_PRE_SWALLOW_BITE}

