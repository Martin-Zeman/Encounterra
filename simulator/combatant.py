import copy
import hashlib

import logging
import random
import math
from contextlib import contextmanager

from .abilities.action_surge import ActionSurgeFactory
from .abilities.on_hit_sneak_attack import OnHitSneakAttack
from .abilities.rage import RageFactory
from .action_resolver import check_concentration
from .actions.action_surge_plan_strategy import ActionSurgePlanStrategy
from .actions.actoid import FactoryFlags
from .actions.attack import Attack, AttackFactory
from .actions.default_action_plan_strategy import DefaultActionPlanStrategy
from .actions.melee_attack import MeleeAttackFactory
from .actions.menacing_melee_attack import MenacingMeleeAttackFactory
from .actions.menacing_ranged_attack import MenacingRangedAttackFactory
from .actions.moon_druid_action_plan_strategy import MoonDruidActionPlanStrategy
from .actions.nop import NopFactory
from .actions.precision_melee_attack import PrecisionMeleeAttackFactory
from .actions.precision_ranged_attack import PrecisionRangedAttackFactory
from .actions.ranged_attack import RangedAttackFactory
from .battle_map import Map
from .effects.action_enabler_effect import ActionEnablerEffect
from .effects.effect import EffectType
from .effects.regeneration_effect import RegenerationEffect
from .misc import SavingThrow, Size, SpellcastingResourceType, Class, get_num_superiority_dice
from .conditions import Conditions, is_affected_by, remove_condition
from .actions.dodge import DodgeFactory
from .actions.disengage import DisengageFactory
from .actions.action_constants import TO_FACTORY, TO_HASTED, TO_QUICKENED, TO_TWINNED
from .actions.action_types import Passive, Action, BonusAction, Reaction, HasteAction, MetaAction, FreeAction
from .proto_combatant import ProtoCombatant
from .resources import ResourceDepletionLevel, Uses, ResourceRefreshType
from .spellslots import spellslot_factory

logger = logging.getLogger("Encounterra")


class Combatant(ProtoCombatant):

    name = ""
    cls = None
    level = 0
    id = 0

    def __init__(self, num_or_name, hp, ac, init_bonus, spell_to_hit, speed, dc, resistances=set(), immunities=[], vulnerabities=[]):
        if type(num_or_name) is int:
            self.name = type(self).name + f" ({num_or_name})"
        else:
            self.name = num_or_name  # Wildshape case
        self.action_factories = [(Action.DODGE, DodgeFactory(self)), (Action.DISENGAGE, DisengageFactory(Action.DISENGAGE, self)), (Action.NOP, NopFactory(Action.NOP, self))]
        self.dodge_factory = self.action_factories[0]
        self.disengage_factory = self.action_factories[1]
        self.bonus_action_factories = [(BonusAction.NOP, NopFactory(BonusAction.NOP, self))]
        self.reaction_factories = []
        self.free_action_factories = []
        self.danger_zone_attack = None
        self.haste_action_factories = []
        self.action_plan_strategy = DefaultActionPlanStrategy(self)
        self.passive = []
        self.max_hp = hp
        self.curr_hp = hp
        self.max_hp_modifier = 0
        self.temporary_hp = 0
        self.ac = ac
        self.dc = dc
        self.init_bonus = init_bonus
        self.spell_to_hit = spell_to_hit
        self.aoo_factory = None
        self.pam_factory = None
        self.ability_dmg_bonus = 0
        self.curr_init = None
        self.has_action = True
        self.has_bonus_action = True
        self.has_reaction = True
        self.has_haste_action = False
        self.resources = dict()
        self.speed = speed // 5
        self.movement = speed // 5
        self.ammo = {}  # Dict of type Attack Factory Name -> current ammo, TODO: Unify with resources
        self.resistances = resistances
        self.immunities = immunities
        self.vulnerabities = vulnerabities
        self.attack_fsm = None
        self.proto_dag = None
        self.action_plan = None
        self.team_color = ""
        self.melee_reaction_range = 1
        self.action_resolver = None
        self.disadvantage_on_incoming_attacks = False
        # maps saving_throw_type -> (bonus, RollType)
        self.saving_throws = {SavingThrow.STR: 0, SavingThrow.DEX: 0,
                              SavingThrow.CON: 0, SavingThrow.INT: 0,
                              SavingThrow.WIS: 0,
                              SavingThrow.CHA: 0}
        self.athletics = 0
        self.acrobatics = 0
        self.stealth = 0
        self.has_pack_tactics = False
        self.passive_perception = 10
        self.conditions = []
        self.dc_conditions = []
        self.is_dodging = False  # TODO reconcile this somehow with disadvantage_on_incoming_attacks
        self.has_disengaged = False  # TODO Get rid of this
        self.spellslots = None
        self.concentration_effect = None
        self.already_cast_leveled_spell_this_turn = False
        self.shield_spell_active = False
        self.size = Size.MEDIUM
        self.saving_throws_flat_mod = {SavingThrow.STR: [0], SavingThrow.DEX: [0], SavingThrow.CON: [0], SavingThrow.INT: [0], SavingThrow.WIS: [0], SavingThrow.CHA: [0]}
        self.saving_throws_dice_mod = {SavingThrow.STR: [], SavingThrow.DEX: [], SavingThrow.CON: [], SavingThrow.INT: [], SavingThrow.WIS: [], SavingThrow.CHA: []}
        self.saving_throws_roll_type_mod = {SavingThrow.STR: set(), SavingThrow.DEX: set(), SavingThrow.CON: set(), SavingThrow.INT: set(), SavingThrow.WIS: set(), SavingThrow.CHA: set()}
        self.to_hit_flat_mod = 0
        self.to_hit_dice_mod = []  # In string format for easier removal
        self.shortest_paths_cache = None
        self.wears_metal = False
        self.is_humanoid = type(type(self).cls) is not Class.MONSTER or type(self).cls is Class.MONSTER.HUMANOID
        self.constricted_target = None
        self.swallowed_target = None
        self.is_swallowed = [False, None]  # [if swallowed, by whom]
        self.uncanny_dodge_active = False
        self.display_abilities = []
        self.dmg_types_took_last_round = set()
        self.one_time_ac_bonus = 0
        self.current_wildshape_form = None
        self.original_form = self
        self.weapon_dmg_dealt_this_turn = 0

    @staticmethod
    def generate_unique_id(name, cls, level):
        unique_str = f"{name}-{cls}-{level}"
        hash_digest = hashlib.sha256(unique_str.encode()).hexdigest()
        return int(hash_digest[:8], 16)

    def __str__(self):
        return self.name

    def is_alive(self):
        return self.curr_hp > 0

    def on_die(self):
        pass

    def on_end_of_turn(self):
        self.dmg_types_took_last_round.clear()

    def roll_initiative(self):
        self.curr_init = random.randint(1, 20) + self.init_bonus

    def get_current_form(self):
        return self if self.current_wildshape_form is None else self.current_wildshape_form

    def get_original_form(self):
        return self.original_form

    def add_ability(self, action_type, **kwargs):
        """

        :param action_type: one of Action, BonusAction, Reaction or Passive instances
        :param kwargs: holds the resources that the action_type needs. They are to be stored in this instance. It also holds any information
        that cannot be directly determined by the action_type (such as a level-specific modifier)
        :return: The factory that has been added or None if case of passive actions factories, AoO or errors
        """
        # TODO Consider removing the kwargs and derive everything from the level
        if isinstance(action_type, Passive):
            match action_type:
                case Passive.SPELLCASTING:
                    spell_resource_type = kwargs.get('resource_type', None)
                    if not spell_resource_type:
                        logger.error("No spell resource type defined!")
                        return None
                    if spell_resource_type is SpellcastingResourceType.SPELLSLOTS:
                        spellslot_cls = kwargs.get('cls', None)
                        if spellslot_cls:
                            self.spellslots = spellslot_factory(spellslot_cls, self.level)
                        else:
                            self.spellslots = spellslot_factory(type(self).cls, self.level)
                        self.resources[Passive.SPELLCASTING] = self.spellslots  # TODO remove the above
                    # elif spell_resource_type is SpellcastingResourceType.SPECIAL:
                    #     resource = kwargs.get('resource', None)
                    #     if not resource:
                    #         logger.error("No spellcasting resource defined!")
                    #         return None
                    #     self.resources.append(resource)
                    # else:
                    #     logger.error("Unknown spellcasting resource type!")
                    #     return None

                    # self.display_abilities.append("Spellcasting")
                case Passive.METAMAGIC:
                    sorcery_points = Uses(self.level, ResourceRefreshType.LONG_REST)
                    self.resources[Passive.METAMAGIC] = sorcery_points
                    self.display_abilities.append("Metamagic")
                case Passive.PACK_TACTICS:
                    self.has_pack_tactics = True
                    self.display_abilities.append("Pack Tactics")
                case Passive.FANATIC_ADVANTAGE:
                    self.already_used_fanatic_advantage = False
                    self.display_abilities.append("Fanatic Advantage")
                case Passive.CUNNING_ACTION:
                    self.add_ability(BonusAction.CUNNING_DISENGAGE)
                    self.add_ability(BonusAction.CUNNING_DASH)
                    self.add_ability(BonusAction.CUNNING_HIDE)
                    self.display_abilities.append("Cunning Action")
                case Passive.SNEAK_ATTACK:
                    self.already_used_sneak_attack_this_turn = False
                    for af in self.action_factories:
                        if FactoryFlags.IS_ATTACK_LIKE in af[1].flags and (FactoryFlags.USES_DEX in af[1].flags or FactoryFlags.IS_RANGED in af[1].flags):
                            af[1].on_hit.append(OnHitSneakAttack(OnHitSneakAttack.get_dmg_dice(self.level), af[1].dmg_type, af[1].crit_range))
                    for baf in self.bonus_action_factories:
                        if FactoryFlags.IS_ATTACK_LIKE in baf[1].flags and (FactoryFlags.USES_DEX in baf[1].flags or FactoryFlags.IS_RANGED in baf[1].flags):
                            baf[1].on_hit.append(OnHitSneakAttack(OnHitSneakAttack.get_dmg_dice(self.level), baf[1].dmg_type, baf[1].crit_range))
                    for haf in self.haste_action_factories:
                        if FactoryFlags.IS_ATTACK_LIKE in haf[1].flags and (FactoryFlags.USES_DEX in haf[1].flags or FactoryFlags.IS_RANGED in haf[1].flags):
                            haf[1].on_hit.append(OnHitSneakAttack(OnHitSneakAttack.get_dmg_dice(self.level), haf[1].dmg_type, haf[1].crit_range))
                    for raf in self.reaction_factories:
                        if FactoryFlags.IS_ATTACK_LIKE in raf[1].flags and (FactoryFlags.USES_DEX in raf[1].flags or FactoryFlags.IS_RANGED in raf[1].flags):
                            raf[1].on_hit.append(OnHitSneakAttack(OnHitSneakAttack.get_dmg_dice(self.level), raf[1].dmg_type, raf[1].crit_range))
                    self.display_abilities.append("Sneak Attack")
                case Passive.REGENERATION:
                    try:
                        Map.get().effect_tracker.add(RegenerationEffect(self, kwargs["hp"], kwargs["suppression_dmg_type"]))
                    except AttributeError:
                        pass  # This is ok for the sake of getting all the combatants by the backend
                    self.display_abilities.append("Regeneration")
                case Passive.HEART_OF_HRUGGEK:
                    self.display_abilities.append("Heart of Hruggek")
                case Passive.DARK_DEVOTION:
                    self.display_abilities.append("Dark Devotion")
                case Passive.BLINDSIGHT:
                    self.display_abilities.append("Blindsight")
                case Passive.ASSASSINATE:
                    self.display_abilities.append("Assassinate")
                case Passive.CHARM_IMMUNITY:
                    self.display_abilities.append("Charm Immunity")
                case Passive.BATTLE_MASTER_MANEUVERS:
                    superiority_dice_resource = Uses(get_num_superiority_dice(self.level), ResourceRefreshType.SHORT_REST)
                    self.resources[Passive.BATTLE_MASTER_MANEUVERS] = superiority_dice_resource
                    new_action_factories = []
                    for af in self.action_factories:
                        if isinstance(af[1], AttackFactory):
                            af_kwargs = af[1].get_kwargs()
                            menacing_attack = MenacingMeleeAttackFactory(**af_kwargs) if FactoryFlags.IS_MELEE in af[1].flags else MenacingRangedAttackFactory(**af_kwargs)
                            new_action_factories.append((af[0], menacing_attack))
                            self.ammo[menacing_attack.name] = self.ammo[af[1].name]

                            # af_kwargs = af[1].get_kwargs()
                            # precision_attack = PrecisionMeleeAttackFactory(**af_kwargs) if FactoryFlags.IS_MELEE in af[1].flags else PrecisionRangedAttackFactory(**af_kwargs)
                            # new_action_factories.append((af[0], precision_attack))
                    self.action_factories.extend(new_action_factories)
                    new_bonus_action_factories = []
                    for baf in self.bonus_action_factories:
                        if isinstance(baf[1], AttackFactory):
                            baf_kwargs = baf[1].get_kwargs()
                            menacing_attack = MenacingMeleeAttackFactory(**baf_kwargs) if FactoryFlags.IS_MELEE in baf[1].flags else MenacingRangedAttackFactory(**baf_kwargs)
                            new_bonus_action_factories.append((baf[0], menacing_attack))
                            self.ammo[menacing_attack.name] = self.ammo[baf[1].name]

                            # baf_kwargs = baf[1].get_kwargs()
                            # precision_attack = PrecisionMeleeAttackFactory(**baf_kwargs) if FactoryFlags.IS_MELEE in baf[1].flags else PrecisionRangedAttackFactory(**baf_kwargs)
                            # new_bonus_action_factories.append((baf[0], precision_attack))
                    self.bonus_action_factories.extend(new_bonus_action_factories)
                    self.display_abilities.append("Riposte")
                    self.display_abilities.append("Precision Attack")
                    self.display_abilities.append("Menacing Attack")
                case _:
                    pass  # no resources required
            self.passive.append(action_type)
            return None
        elif isinstance(action_type, Action):
            match action_type:
                case Action.MELEE_ATTACK | Action.RANGED_ATTACK | Action.RECKLESS_ATTACK | Action.PRE_SWALLOW_BITE \
                     | Action.BITE_AND_SWALLOW | Action.VAMPIRIC_BITE:
                    factory = TO_FACTORY[action_type]
                    try:
                        suppress = kwargs.pop("suppress")
                    except KeyError:
                        suppress = False
                    self.action_factories.append((action_type, factory(**kwargs, action_type=action_type)))
                    just_added = self.action_factories[-1]
                    self.ammo[just_added[1].name] = just_added[1].ammo
                    if not suppress:
                        self.display_abilities.append(just_added[1].name)
                    return just_added
                case Action.GRAPPLE_ATTACK:
                    self.action_factories.append((action_type, TO_FACTORY[action_type](**kwargs, action_type=action_type)))
                    self.display_abilities.append(self.action_factories[-1][1].get_ability_name())
                    return self.action_factories[-1]
                case Action.FIREBALL:
                    resource = kwargs.get("resource", self.spellslots)
                    self.action_factories.append((action_type, TO_FACTORY[action_type](self.dc, action_type, self, resource, has_spell_sculpting=False)))
                    self.display_abilities.append(self.action_factories[-1][1].get_ability_name())
                    return self.action_factories[-1]
                case Action.HOLD_PERSON | Action.FLAMING_SPHERE | Action.FAERIE_FIRE | Action.THUNDERWAVE:
                    resource = kwargs.get("resource", self.spellslots)
                    self.action_factories.append((action_type, TO_FACTORY[action_type](self.dc, action_type, self, resource)))
                    self.display_abilities.append(self.action_factories[-1][1].get_ability_name())
                    return self.action_factories[-1]
                case Action.FIREBOLT | Action.SHOCKING_GRASP | Action.CHAOSBOLT | Action.SCORCHING_RAY:
                    resource = kwargs.get("resource", self.spellslots)
                    self.action_factories.append((action_type, TO_FACTORY[action_type](self.spell_to_hit, action_type, self, resource)))
                    self.display_abilities.append(self.action_factories[-1][1].get_ability_name())
                    return self.action_factories[-1]
                case Action.MAGIC_MISSILE | Action.HASTE | Action.BLESS | Action.RAY_OF_ENFEEBLEMENT | Action.SLEEP:
                    resource = kwargs.get("resource", self.spellslots)
                    self.action_factories.append((action_type, TO_FACTORY[action_type](action_type, self, resource)))
                    self.display_abilities.append(self.action_factories[-1][1].get_ability_name())
                    return self.action_factories[-1]
                case Action.DISENGAGE:
                    self.action_factories.append((action_type, TO_FACTORY[action_type](action_type, self)))
                    return self.action_factories[-1]
                case Action.WILDSHAPE:
                    wildshape_uses = Uses(TO_FACTORY[action_type].get_wildshape_uses(self.level), ResourceRefreshType.SHORT_REST)
                    self.resources[Action.WILDSHAPE] = wildshape_uses
                    self.action_factories.append((action_type, TO_FACTORY[action_type](self)))
                    self.display_abilities.append("Wildshape")
                    # def wildshape_get(self):
                    #     return self if self.current_wildshape_form is None else self.current_wildshape_form
                    # self.get_current_form = wildshape_get.__get__(self, Combatant)
                    return self.action_factories[-1]
                case Action.POUNCE:
                    self.action_factories.append((action_type, TO_FACTORY[action_type](**kwargs)))
                    self.display_abilities.append(self.action_factories[-1][1].get_ability_name())
                    return self.action_factories[-1]
                case Action.CONSTRICT:
                    self.constricted_target = None
                    self.action_factories.append((action_type, TO_FACTORY[action_type](**kwargs)))
                    self.display_abilities.append(self.action_factories[-1][1].get_ability_name())
                    return self.action_factories[-1]
                case _:
                    return None
        elif isinstance(action_type, BonusAction):
            # TODO
            match action_type:
                case BonusAction.BONUS_MELEE_ATTACK | BonusAction.BONUS_RANGED_ATTACK:
                    factory = TO_FACTORY[action_type]
                    self.bonus_action_factories.append((action_type, factory(**kwargs, action_type=action_type)))
                    just_added = self.bonus_action_factories[-1]
                    self.ammo[just_added[1].name] = just_added[1].ammo
                    self.display_abilities.append(just_added[1].name)
                    return just_added
                case BonusAction.PAM_BONUS_ATTACK:
                    self.bonus_action_factories.append((action_type, TO_FACTORY[action_type](**kwargs, action_type=action_type)))
                    self.pam_factory = self.bonus_action_factories[-1]
                    self.display_abilities.append(self.bonus_action_factories[-1][1].name)
                    return self.bonus_action_factories[-1]
                case BonusAction.RAGE | BonusAction.TOTEM_RAGE:
                    rage_uses = Uses(RageFactory.get_rage_uses(self.level), ResourceRefreshType.LONG_REST)
                    self.resources[action_type] = rage_uses
                    self.bonus_action_factories.append((action_type, TO_FACTORY[action_type](self)))
                    self.display_abilities.append(self.bonus_action_factories[-1][1].get_ability_name())
                    return self.bonus_action_factories[-1]
                case BonusAction.SECOND_WIND:
                    second_wind_uses = Uses(1, ResourceRefreshType.SHORT_REST)
                    self.resources[BonusAction.SECOND_WIND] = second_wind_uses
                    self.bonus_action_factories.append((action_type, TO_FACTORY[action_type](self)))
                    self.display_abilities.append(self.bonus_action_factories[-1][1].get_ability_name())
                    return self.bonus_action_factories[-1]
                case BonusAction.MISTY_STEP:
                    resource = kwargs.get("resource", self.spellslots)
                    self.bonus_action_factories.append((action_type, TO_FACTORY[action_type](self, resource)))
                    self.display_abilities.append(self.bonus_action_factories[-1][1].get_ability_name())
                    return self.bonus_action_factories[-1]
                case BonusAction.CUNNING_DISENGAGE | BonusAction.CUNNING_HIDE | BonusAction.CUNNING_DASH:
                    self.bonus_action_factories.append((action_type, TO_FACTORY[action_type](action_type, self)))  # TODO
                    return self.bonus_action_factories[-1]
                case BonusAction.QUICKENED_FIREBALL | BonusAction.QUICKENED_THUNDERWAVE:
                    resource = kwargs.get("resource", self.spellslots)
                    self.bonus_action_factories.append(
                        (action_type, TO_FACTORY[action_type](self.dc, action_type, self, resource, has_spell_sculpting=False)))
                    return self.bonus_action_factories[-1]
                case BonusAction.QUICKENED_FIREBOLT | BonusAction.QUICKENED_SHOCKING_GRASP | BonusAction.QUICKENED_CHAOSBOLT | BonusAction.QUICKENED_SCORCHING_RAY:
                    resource = kwargs.get("resource", self.spellslots)
                    self.bonus_action_factories.append(
                        (action_type, TO_FACTORY[action_type](self.spell_to_hit, action_type, self, resource)))
                    return self.bonus_action_factories[-1]
                case BonusAction.QUICKENED_HASTE:
                    resource = kwargs.get("resource", self.spellslots)
                    self.bonus_action_factories.append(
                        (action_type, TO_FACTORY[action_type](action_type, self, resource)))
                    return self.bonus_action_factories[-1]
                case BonusAction.MOON_WILDSHAPE:
                    wildshape_uses = Uses(TO_FACTORY[action_type].get_wildshape_uses(self.level), ResourceRefreshType.SHORT_REST)
                    self.resources[Action.WILDSHAPE] = wildshape_uses  # Yes, this is WILDSHAPE on purpose, it makes resource management easier
                    self.bonus_action_factories.append((action_type, TO_FACTORY[action_type](self, action_type)))
                    # def wildshape_get(self):
                    #     return self if self.current_wildshape_form is None else self.current_wildshape_form
                    # self.get_current_form = wildshape_get.__get__(self, Combatant)
                    self.display_abilities.append(self.bonus_action_factories[-1][1].get_ability_name())
                    self.action_plan_strategy = MoonDruidActionPlanStrategy(self)
                    return self.bonus_action_factories[-1]
                case BonusAction.SHILLELAGH:
                    resource = kwargs.get("resource", self.spellslots)
                    self.bonus_action_factories.append((action_type, TO_FACTORY[action_type](self, resource, **kwargs)))
                    self.display_abilities.append(self.bonus_action_factories[-1][1].get_ability_name())
                case BonusAction.HEALING_WORD:
                    resource = kwargs.get("resource", self.spellslots)
                    self.bonus_action_factories.append((action_type, TO_FACTORY[action_type](self.spell_to_hit, self, resource, **kwargs)))
                    self.display_abilities.append(self.bonus_action_factories[-1][1].get_ability_name())
                case _:
                    pass  # no resources required
        elif isinstance(action_type, Reaction):
            match action_type:
                case Reaction.REACTION_ATTACK | Reaction.PRE_SWALLOW_BITE_REACTION:
                    self.reaction_factories.append((action_type, TO_FACTORY[action_type](**kwargs, action_type=action_type)))
                    self.aoo_factory = self.reaction_factories[-1]
                    self.danger_zone_attack = self.reaction_factories[-1]  # By default this is set to the reaction attack
                    self.melee_reaction_range = self.aoo_factory[1].range
                    return None
                case Reaction.SHIELD:
                    resource = kwargs.get("resource", self.spellslots)
                    self.reaction_factories.append((action_type, TO_FACTORY[action_type](self, resource)))
                    self.display_abilities.append(self.reaction_factories[-1][1].get_ability_name())
                    return self.reaction_factories[-1]
                case Reaction.UNCANNY_DODGE:
                    self.reaction_factories.append((action_type, TO_FACTORY[action_type](self)))
                    self.display_abilities.append(self.reaction_factories[-1][1].get_ability_name())
                    return self.reaction_factories[-1]
                case Reaction.PARRY:
                    self.reaction_factories.append((action_type, TO_FACTORY[action_type](**kwargs)))
                    self.display_abilities.append(self.reaction_factories[-1][1].get_ability_name() + f" : {kwargs['ac']}")
                    return self.reaction_factories[-1]
                case _:
                    logger.error("Unknown reaction")
                    return None
        elif isinstance(action_type, HasteAction):
            # TODO Remove this
            for action in self.action_factories:
                try:
                    # A combatant can have multiple attacks, we need a hastened version of all of them
                    hasted_action = TO_HASTED[action]
                    self.haste_action_factories.append((hasted_action, copy.deepcopy(action)))  # Need a copy to change the action_type
                    self.haste_action_factories[-1].action_type = action_type
                    return None
                except KeyError:
                    pass
            return None
        elif isinstance(action_type, MetaAction):
            match action_type:
                case MetaAction.QUICKENED_SPELL:
                    assert Passive.METAMAGIC in self.passive
                    for af in self.action_factories:
                        try:
                            quickened_action = TO_QUICKENED[af[0]]
                            quickened_action_factory = TO_FACTORY[quickened_action]
                            qaf_kwargs = af[1].get_quickened_kwargs()
                            qaf_kwargs['action_type'] = quickened_action
                            self.bonus_action_factories.append((quickened_action, quickened_action_factory(**qaf_kwargs)))
                        except KeyError:
                            pass
                case MetaAction.TWINNED_SPELL:
                    assert Passive.METAMAGIC in self.passive
                    for af in self.action_factories:
                        try:
                            twinned_action = TO_TWINNED[af[0]]
                            twinned_action_factory = TO_FACTORY[twinned_action]
                            taf_kwargs = af[1].get_twinned_kwargs()
                            taf_kwargs['action_type'] = twinned_action
                            self.action_factories.append((twinned_action, twinned_action_factory(**taf_kwargs)))
                        except KeyError:
                            pass
                    for baf in self.bonus_action_factories:
                        try:
                            twinned_bonus_action = TO_TWINNED[baf[0]]
                            twinned_bonus_action_factory = TO_FACTORY[twinned_bonus_action]
                            tbaf_kwargs = af[1].get_twinned_kwargs()
                            tbaf_kwargs['action_type'] = twinned_bonus_action
                            self.bonus_action_factories.append((twinned_bonus_action, twinned_bonus_action_factory(**tbaf_kwargs)))
                        except KeyError:
                            pass
                    return None  # There can be multiple ones here, cannot return them all
                case MetaAction.EMPOWERED_SPELL:
                    assert Passive.METAMAGIC in self.passive
                    return None
                    # TODO
                case _:
                    logger.error("Unknown meta action")
                    return None
        elif isinstance(action_type, FreeAction):
            match action_type:
                case FreeAction.ACTION_SURGE:
                    action_surge_uses = Uses(ActionSurgeFactory.get_action_surge_uses(self.level), ResourceRefreshType.SHORT_REST)
                    self.resources[FreeAction.ACTION_SURGE] = action_surge_uses
                    self.free_action_factories.append((action_type, TO_FACTORY[action_type](self)))
                    self.display_abilities.append(self.free_action_factories[-1][1].get_ability_name())
                    self.action_plan_strategy = ActionSurgePlanStrategy(self)
                    return self.free_action_factories[-1]
                case _:
                    logger.error("Unknown free action")
                    return None
        else:
            logger.error("Unknown high level action class")
            return None

    def add_hasted_factories(self):
        for af in self.action_factories:
            try:
                hasted_action = TO_HASTED[af[0]]
                hasted_action_factory = TO_FACTORY[hasted_action]
                haf_kwargs = af[1].get_kwargs()
                haf_kwargs['action_type'] = hasted_action
                self.haste_action_factories.append((hasted_action, hasted_action_factory(**haf_kwargs)))
            except KeyError:
                pass

    def has_passive(self, ability):
        return ability in self.passive

    def _receive_dmg(self, dmg, dmg_type):
        """
        Private-like function which takes care of receiving dmg but does not incur a concentration check
        :param dmg: amount dmg to be received
        :param dmg_type: damage type
        :return: actual dmg received accounting for resistances, vulnerabilities and immunities
        """
        if dmg_type in self.immunities:
            return 0
        elif dmg_type in self.resistances:
            dmg = math.floor(dmg / 2)
            logger.info(f"{self.name} is resistant to {dmg_type} and reduces the damage to {dmg}")
        elif dmg_type in self.vulnerabities:
            dmg *= 2
            logger.info(f"{self.name} is vulnerable to {dmg_type} which doubles the damage to {dmg}")
        if self.uncanny_dodge_active:
            dmg = math.floor(dmg / 2)
            logger.info(f"{self.name} uses Uncanny Dodge which reduces the damage to {dmg}")
        assert self.temporary_hp >= 0  # TODO Remove this
        self.temporary_hp -= dmg
        if self.temporary_hp < 0:
            self.curr_hp += self.temporary_hp
            self.temporary_hp = 0
        self.dmg_types_took_last_round.add(dmg_type)
        return dmg

    def receive_dmg(self, dmg, dmg_type):
        """
        Inflicts damage to the combatant
        :param dmg: amount dmg to be received
        :param dmg_type: damage type
        :return: actual dmg received accounting for resistances, vulnerabilities and immunities
        """
        dmg = self._receive_dmg(dmg, dmg_type)
        battle_map = Map.get()
        if self.curr_hp <= 0 and self.get_original_form() is not self:
            self.get_original_form().curr_hp += self.curr_hp  # carry-over damage
            battle_map.effect_tracker.remove_effect_from_combatant_by_type(self.get_original_form(), EffectType.WILDSHAPE)
        if dmg:
            check_concentration(self, dmg)
            if is_affected_by(self, Conditions.AWAKENED_BY_DMG):
                cond = remove_condition(self, Conditions.AWAKENED_BY_DMG)
                logger.info(f"{self} is awakened by taking damage")
                if cond.effect:
                    battle_map.effect_tracker.remove_effect_from_combatant(self, cond.effect)
        return dmg

    def receive_compound_dmg(self, dmg):
        """
        Inflicts damage to the combatant composed of different damage types
        :param dmg: lift of tuples: [(dmg, dmg_type), ...]
        :return: actual dmg received accounting for resistances, vulnerabilities and immunities
        """
        total_dmg = 0
        for d in dmg:
            total_dmg += self._receive_dmg(d[0], d[1])
        battle_map = Map.get()
        if self.curr_hp <= 0 and self.get_original_form() is not self:
            self.get_original_form().curr_hp += self.curr_hp  # carry-over damage
            battle_map.effect_tracker.remove_effect_from_combatant_by_type(self.get_original_form(), EffectType.WILDSHAPE)
        if total_dmg:
            check_concentration(self, total_dmg)
            if is_affected_by(self, Conditions.AWAKENED_BY_DMG):
                cond = remove_condition(self, Conditions.AWAKENED_BY_DMG)
                logger.info(f"{self} is awakened by taking damage")
                if cond.effect:
                    battle_map.effect_tracker.remove_effect_from_combatant(self, cond.effect)
        self.uncanny_dodge_active = False
        return total_dmg

    def heal(self, hp):
        self.curr_hp = min(self.curr_hp + hp, self.max_hp + self.max_hp_modifier)

    def is_resistant_to(self, dmg_type):
        return dmg_type in self.resistances

    def is_immune_to(self, dmg_type):
        return dmg_type in self.immunities

    def is_vulnerable_to(self, dmg_type):
        return dmg_type in self.vulnerabities

    def new_turn(self):
        self.has_action = True
        self.has_bonus_action = True
        self.has_reaction = True
        self.movement = self.speed
        # if self.is_dodging:
        #     self.saving_throws_roll_type_mod[SavingThrow.DEX].add(RollType.STRAIGHT)
        # self.is_dodging = False # TODO make sure the effect tracker takes care of this
        self.already_cast_leveled_spell_this_turn = False
        if self.shield_spell_active:
            self.ac -= 5
        self.shield_spell_active = False
        self.has_haste_action = False
        self.attack_fsm.set_state('0')
        self.action_plan = None
        if self.constricted_target and not self.constricted_target.is_alive():
            self.constricted_target = None
        self.weapon_dmg_dealt_this_turn = 0

    def reset(self):
        self.has_action = True
        self.has_bonus_action = True
        self.has_reaction = True
        self.curr_hp = self.max_hp
        self.movement = self.speed
        self.is_dodging = False
        if self.spellslots:
            self.spellslots.reset()
        for r in self.resources.values():
            r.reset()
        self.already_cast_leveled_spell_this_turn = False
        if self.shield_spell_active:
            self.ac -= 5
        self.shield_spell_active = False
        self.conditions.clear()
        self.dc_conditions.clear()
        self.concentration_effect = None
        self.has_haste_action = False
        self.saving_throws_flat_mod = dict.fromkeys(self.saving_throws_flat_mod.keys(), 0)
        self.saving_throws_dice_mod = dict.fromkeys(self.saving_throws_dice_mod.keys(), [])
        self.saving_throws_roll_type_mod = dict.fromkeys(self.saving_throws_roll_type_mod.keys(), set())
        for ammo in self.ammo.values():
            ammo.reset()
        self.one_time_ac_bonus = 0  # Not really needed

    def deplete_resources(self, level: ResourceDepletionLevel):
        for r in self.resources.values():
            r.deplete_resource(level)

    @contextmanager
    def as_if_used_action_enabler(self, action):
        if isinstance(action, ActionEnablerEffect):
            try:
                action.enable()
                yield True
            finally:
                action.disable()
        else:
            yield False

    def export_resources(self):
        return None

    def import_resources(self, resources):
        pass

    @contextmanager
    def as_if_has_action(self):
        has_action = self.has_action
        try:
            self.has_action = True
        finally:
            yield self
        self.has_action = has_action

    def add_team(self, team_color):
        self.team_color = team_color

    def prompt_aoo(self, moving_combatant):
        return None

    def prompt_pam(self, moving_combatant):
        return None

    def prompt_attack_reaction(self, attacking_combatant, attack_roll):
        return None

    def prompt_dmg_reaction(self, attacking_combatant, dmg, dmg_type):
        return None

    def prompt_after_hit_reaction(self, attacker, attack, attack_roll):
        return None

    def prompt_after_miss_reaction(self, attacker):
        return None

    def calculate_action_plan(self, distances, shortest_paths):
        """
        A thin wrapper for the calculation of action plan
        :param distances: the distances to all squares (result of Dijkstra)
        :param shortest_paths: the shortest paths to all squares (result of Dijkstra)
        :return: the action plan
        """
        return self.action_plan_strategy.calculate_action_plan(distances, shortest_paths)

    def break_concentration(self):
        self.get_current_form().concentration_effect = None
        self.get_original_form().concentration_effect = None
