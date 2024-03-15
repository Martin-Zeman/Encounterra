import logging

from .grapple_attack import GrappleAttackFactory
from .parry import ParryFactory
from .vampiric_bite import VampiricBiteFactory
from ..abilities.action_surge import ActionSurgeFactory
from ..abilities.bite_and_swallow import BiteAndSwallowFactory
from ..abilities.pre_swallow_bite import PreSwallowBiteFactory
from ..abilities.constrict import ConstrictFactory
from ..abilities.pounce import PounceFactory
from ..abilities.rage import RageFactory
from ..abilities.reckless_attack import RecklessAttackFactory
from ..abilities.second_wind import SecondWindFactory
from ..abilities.totem_rage import TotemRageFactory
from ..abilities.uncanny_dodge import UncannyDodgeFactory
from ..abilities.wildshape import WildshapeFactory
from ..actions.action_types import Action, BonusAction, HasteAction, Reaction, MovementThreatType, FreeAction
from ..actions.dash import DashFactory
from ..actions.disengage import DisengageFactory
from ..actions.dodge import DodgeFactory
from ..actions.hide import HideFactory
from ..actions.melee_attack import MeleeAttackFactory
from ..actions.ranged_attack import RangedAttackFactory
from ..spells.bless import BlessFactory
from ..spells.chaosbolt import ChaosboltFactory
from ..spells.faerie_fire import FaerieFireFactory
from ..spells.fireball import FireballFactory
from ..spells.firebolt import FireboltFactory
from ..spells.flaming_sphere import FlamingSphereFactory
from ..spells.haste import HasteFactory
from ..spells.hold_person import HoldPersonFactory
from ..spells.magic_missile import MagicMissileFactory
from ..spells.ray_of_enfeeblement import RayOfEnfeeblementFactory
from ..spells.shocking_grasp import ShockingGraspFactory
from ..spells.sleep import SleepFactory
from ..spells.thunderwave import ThunderwaveFactory
from ..spells.twinned_hold_person import TwinnedHoldPersonFactory
from ..spells.misty_step import MistyStepFactory
from ..spells.scorching_ray import ScorchingRayFactory
from ..spells.shield import ShieldFactory
from ..spells.twinned_firebolt import TwinnedFireboltFactory
from ..spells.twinned_haste import TwinnedHasteFactory
from ..spells.twinned_ray_of_enfeeblement import TwinnedRayOfEnfeeblementFactory

logger = logging.getLogger("Encounterra")

PRIORITY_ACTIONS = {
    Action.DODGE: ("do_", MovementThreatType.DODGED),
    Action.DISENGAGE: ("di_", MovementThreatType.DISENGAGED),
    HasteAction.HASTE_DISENGAGE: ("hdi_", MovementThreatType.DISENGAGED)
}

PRIORITY_BONUS_ACTIONS = {
    BonusAction.CUNNING_DISENGAGE: ("cdi_", MovementThreatType.DISENGAGED),
    BonusAction.TOTEM_RAGE: ("m_", MovementThreatType.STANDARD),
    BonusAction.RAGE: ("m_", MovementThreatType.STANDARD),
}

TO_FACTORY = {
    Action.MELEE_ATTACK: MeleeAttackFactory,
    Action.RANGED_ATTACK: RangedAttackFactory,
    Action.RECKLESS_ATTACK: RecklessAttackFactory,
    Action.DODGE: DodgeFactory,
    Action.DASH: DashFactory,
    Action.DISENGAGE: DisengageFactory,
    Action.FIREBALL: FireballFactory,
    Action.FIREBOLT: FireboltFactory,
    Action.CHAOSBOLT: ChaosboltFactory,
    Action.HASTE: HasteFactory,
    Action.HIDE: HideFactory,
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
    Action.SHOCKING_GRASP: ShockingGraspFactory,
    Action.TWINNED_SHOCKING_GRASP: ShockingGraspFactory,
    Action.MAGIC_MISSILE: MagicMissileFactory,
    Action.FAERIE_FIRE: FaerieFireFactory,
    Action.GRAPPLE_ATTACK: GrappleAttackFactory,
    Action.VAMPIRIC_BITE: VampiricBiteFactory,
    Action.BLESS: BlessFactory,
    Action.RAY_OF_ENFEEBLEMENT: RayOfEnfeeblementFactory,
    Action.TWINNED_RAY_OF_ENFEEBLEMENT: TwinnedRayOfEnfeeblementFactory,
    Action.SLEEP: SleepFactory,
    Action.THUNDERWAVE: ThunderwaveFactory,

    BonusAction.BONUS_MELEE_ATTACK: MeleeAttackFactory,
    BonusAction.BONUS_RANGED_ATTACK: RangedAttackFactory,
    BonusAction.PAM_BONUS_ATTACK: MeleeAttackFactory,
    BonusAction.RAGE: RageFactory,
    BonusAction.TOTEM_RAGE: TotemRageFactory,
    BonusAction.MISTY_STEP: MistyStepFactory,
    BonusAction.CUNNING_DISENGAGE: DisengageFactory,
    BonusAction.CUNNING_HIDE: HideFactory,
    BonusAction.CUNNING_DASH: DashFactory,
    BonusAction.QUICKENED_FIREBALL: FireballFactory,
    BonusAction.QUICKENED_FIREBOLT: FireboltFactory,
    BonusAction.QUICKENED_CHAOSBOLT: ChaosboltFactory,
    BonusAction.QUICKENED_HASTE: HasteFactory,
    BonusAction.QUICKENED_SCORCHING_RAY: ScorchingRayFactory,
    BonusAction.MOON_WILDSHAPE: WildshapeFactory,
    BonusAction.QUICKENED_HOLD_PERSON: HoldPersonFactory,
    BonusAction.QUICKENED_SHOCKING_GRASP: ShockingGraspFactory,
    BonusAction.QUICKENED_MAGIC_MISSILE: MagicMissileFactory,
    BonusAction.QUICKENED_FAERIE_FIRE: FaerieFireFactory,
    BonusAction.QUICKENED_BLESS: BlessFactory,
    BonusAction.QUICKENED_RAY_OF_ENFEEBLEMENT: RayOfEnfeeblementFactory,
    BonusAction.QUICKENED_SLEEP: SleepFactory,
    BonusAction.SECOND_WIND: SecondWindFactory,
    BonusAction.QUICKENED_THUNDERWAVE: ThunderwaveFactory,

    Reaction.SHIELD: ShieldFactory,
    Reaction.REACTION_ATTACK: MeleeAttackFactory,
    Reaction.PRE_SWALLOW_BITE_REACTION: PreSwallowBiteFactory,
    Reaction.UNCANNY_DODGE: UncannyDodgeFactory,
    Reaction.PARRY: ParryFactory,

    HasteAction.HASTE_MELEE_ATTACK: MeleeAttackFactory,
    HasteAction.HASTE_PRE_SWALLOW_BITE: PreSwallowBiteFactory,
    HasteAction.HASTE_BITE_AND_SWALLOW: BiteAndSwallowFactory,
    HasteAction.HASTE_RANGED_ATTACK: RangedAttackFactory,
    HasteAction.HASTE_DISENGAGE: DisengageFactory,
    HasteAction.HASTE_HIDE: HideFactory,
    HasteAction.HASTE_DASH: None,

    FreeAction.ACTION_SURGE: ActionSurgeFactory
}

TO_QUICKENED = {
    Action.FIREBALL: BonusAction.QUICKENED_FIREBALL,
    Action.FIREBOLT: BonusAction.QUICKENED_FIREBOLT,
    Action.CHAOSBOLT: BonusAction.QUICKENED_CHAOSBOLT,
    Action.HASTE: BonusAction.QUICKENED_HASTE,
    Action.SCORCHING_RAY: BonusAction.QUICKENED_SCORCHING_RAY,
    Action.HOLD_PERSON: BonusAction.QUICKENED_HOLD_PERSON,
    Action.SHOCKING_GRASP: BonusAction.QUICKENED_SHOCKING_GRASP,
    Action.MAGIC_MISSILE: BonusAction.QUICKENED_MAGIC_MISSILE,
    Action.BLESS: BonusAction.QUICKENED_BLESS,
    Action.RAY_OF_ENFEEBLEMENT: BonusAction.QUICKENED_RAY_OF_ENFEEBLEMENT
}

TO_TWINNED = {
    Action.FIREBOLT: Action.TWINNED_FIREBOLT,
    Action.HASTE: Action.TWINNED_HASTE,
    Action.HOLD_PERSON: Action.TWINNED_HOLD_PERSON,
    Action.SHOCKING_GRASP: Action.TWINNED_SHOCKING_GRASP,
    Action.RAY_OF_ENFEEBLEMENT: Action.TWINNED_RAY_OF_ENFEEBLEMENT
}

TO_HASTED = {
    Action.MELEE_ATTACK: HasteAction.HASTE_MELEE_ATTACK,
    Action.RANGED_ATTACK: HasteAction.HASTE_RANGED_ATTACK,
    Action.HIDE: HasteAction.HASTE_HIDE,
    Action.DASH: HasteAction.HASTE_DASH,
    Action.DISENGAGE: HasteAction.HASTE_DISENGAGE,
    Action.BITE_AND_SWALLOW: HasteAction.HASTE_BITE_AND_SWALLOW,
    Action.PRE_SWALLOW_BITE: HasteAction.HASTE_PRE_SWALLOW_BITE,
    Action.GRAPPLE_ATTACK: HasteAction.HASTE_GRAPPLE_ATTACK,
    Action.GRAPPLE: HasteAction.HASTE_GRAPPLE,
    Action.VAMPIRIC_BITE: HasteAction.HASTE_VAMPIRIC_BITE
}

