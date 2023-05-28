from simulator.abilities.pounce import PounceFactory
from simulator.abilities.wildshape import WildshapeFactory
from simulator.actions.attack import Attack
from simulator.actions.dodge import Dodge
from simulator.actions.dash import Dash
from simulator.actions.melee_attack import MeleeAttackFactory
from simulator.actions.ranged_attack import RangedAttackFactory
from simulator.spells.fireball import Fireball
from simulator.spells.firebolt import Firebolt
from simulator.spells.chaosbolt import Chaosbolt
from simulator.spells.scorching_ray import ScorchingRayFactory
from simulator.spells.shield import Shield
from simulator.spells.misty_step import MistyStep
from simulator.spells.haste import Haste
from simulator.abilities.rage import Rage
from simulator.abilities.totem_rage import TotemRage
from simulator.actions.movement import MovementIncrement
from simulator.actions.action_types import *
from simulator.actions.dodge import DodgeFactory
from simulator.actions.disengage import DisengageFactory
from simulator.spells.haste import HasteFactory
from simulator.spells.shield import ShieldFactory
from simulator.spells.fireball import FireballFactory
from simulator.spells.misty_step import MistyStepFactory
from simulator.spells.firebolt import FireboltFactory
from simulator.spells.twinned_firebolt import TwinnedFireboltFactory
from simulator.spells.twinned_haste import TwinnedHasteFactory, TwinnedHaste
from simulator.spells.chaosbolt import ChaosboltFactory
from simulator.abilities.totem_rage import TotemRageFactory
from simulator.abilities.rage import RageFactory
from simulator.abilities.reckless_attack import RecklessAttackFactory
import logging

logger = logging.getLogger("EncounTroll")


# HASTED_ACTIONS = {Action.MELEE_ATTACK, Action.RANGED_ATTACK, Action.HIDE, Action.DASH, Action.DISENGAGE}

# def action_factory(combatant, effect_tracker, action_type, *args):
#     if isinstance(action_type, Action):
#         match action_type:
#             case Action.MELEE_ATTACK | Action.RANGED_ATTACK:
#                 return Attack(action_type, *args)
#             case Action.DODGE:
#                 return Dodge(combatant)
#             case Action.DASH:
#                 return Dash()
#             case Action.FIREBALL:
#                 return Fireball(action_type, *args, combatant.dc)
#             case Action.FIREBOLT:
#                 return Firebolt(action_type, combatant.spell_to_hit, combatant.level, *args)
#             case Action.CHAOSBOLT:
#                 return Chaosbolt(action_type, combatant.spell_to_hit, *args)
#             case Action.HASTE:
#                 return Haste(action_type, *args, combatant, effect_tracker)
#             case Action.TWINNED_FIREBOLT:
#                 logger.info("Twinned Firebolt")
#                 return Firebolt(action_type, combatant.spell_to_hit, combatant.level, *args)
#             case Action.TWINNED_HASTE:
#                 return TwinnedHaste(action_type, *args, combatant, effect_tracker)
#             case _:
#                 logger.error("action_factory: Unknown action type")
#                 return None
#     elif isinstance(action_type, BonusAction):
#         match action_type:
#             case BonusAction.BONUS_MELEE_ATTACK | BonusAction.BONUS_RANGED_ATTACK  | BonusAction.PAM_BONUS_ATTACK:
#                 return Attack(action_type, *args)
#             case BonusAction.TOTEM_RAGE:
#                 return TotemRage(combatant)
#             case BonusAction.RAGE:
#                 return Rage(combatant)
#             case BonusAction.MISTY_STEP:
#                 return MistyStep(*args)
#             case BonusAction.QUICKENED_CHAOSBOLT:
#                 logger.info("Quickened Chaosbolt")
#                 return Chaosbolt(action_type, combatant.spell_to_hit, *args)
#             case BonusAction.QUICKENED_FIREBALL:
#                 logger.info("Quickened Fireball")
#                 return Fireball(action_type, *args, combatant.dc)
#             case BonusAction.QUICKENED_FIREBOLT:
#                 logger.info("Quickened Firebolt")
#                 return Firebolt(action_type, combatant.spell_to_hit, combatant.level, *args)
#             case BonusAction.QUICKENED_HASTE:
#                 return Haste(action_type, *args, combatant, effect_tracker)
#             case _:
#                 logger.error("Unknown bonus action type")
#                 return None
#     elif isinstance(action_type, Reaction):
#         match action_type:
#             case Reaction.REACTION_ATTACK:
#                 return Attack(action_type, *args)
#             case Reaction.SHIELD:
#                 return Shield()
#             case _:
#                 logger.error("Unknown reaction type")
#                 return None
#     elif isinstance(action_type, Movement):
#         match action_type:
#             case Movement.STANDARD:
#                 return MovementIncrement(*args, True)
#             case _:
#                 logger.error("Unknown movement type")
#                 return None
#     elif isinstance(action_type, HasteAction):
#         match action_type:
#             case HasteAction.HASTE_MELEE_ATTACK | HasteAction.HASTE_RANGED_ATTACK:
#                 return Attack(action_type, *args)
#             case HasteAction.HASTE_DASH:
#                 return Dash()
#             case _:
#                 logger.error("Unknown haste action")
#     else:
#         logger.error("Unknown high level action class")
#         return None
