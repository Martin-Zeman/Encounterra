import copy
import random
import math
import inspect
from simulator.actions.actoid import FactoryFlags
from simulator.misc import SavingThrow, Conditions, Size, CombatantArchetype
from simulator.action_factory import *
from enum import Enum
from abc import ABC, abstractmethod
from simulator.abilities.totem_rage import TotemRageFactory
from simulator.actions.attack import AttackFactory
from simulator.actions.dodge import DodgeFactory
from simulator.actions.disengage import DisengageFactory
from simulator.action_factory import TO_TWINNED, TO_QUICKENED

logger = logging.getLogger(__name__)


class Combatant(ABC):
    class State(Enum):
        FINE = 0
        BLOODIED = 1
        NEAR_DEATH = 2

    class ToughnessEstimate(Enum):
        TRASH = 1
        LOW = 2
        MEDIUM = 3
        BOSS = 4


    def __init__(self, effect_tracker, name, level, hp, ac, init_bonus, spell_to_hit, speed, resistances, dc):
        self.effect_tracker = effect_tracker
        self.name = name
        self.level = level
        self.action_factories = [(Action.DODGE, DodgeFactory(self)), (Action.DISENGAGE, DisengageFactory(self, Action.DISENGAGE))]
        self.dodge_factory = self.action_factories[0]
        self.disengage_factory = self.action_factories[1]
        self.bonus_action_factories = []
        self.reaction_factories = []
        self.danger_zone_attack = None
        self.haste_action_factories = []
        self.passive = []
        self.max_hp = hp
        self.curr_hp = hp
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
        self.num_attacks = 1
        self.curr_num_attacks = 1
        self.speed = speed / 5
        self.movement = speed / 5
        self.ammo = {}  # Dict of type Attack Factory Name -> current ammo
        self.resistances = resistances
        self.multiattack_in_progress = False
        self.attack_fsm = None
        self.action_fsm = None
        self.team_color = ""
        self.selected_enemy = None
        self.selected_ally = None
        self.planned_movement = None
        self.movement_generator = None
        self.melee_reaction_range = 1
        self.target_position_cache = None
        self.action_resolver = None
        self.disadvantage_on_incoming_attacks = False
        # maps saving_throw_type -> (bonus, RollModifier)
        self.saving_throws = {SavingThrow.STR: 0, SavingThrow.DEX: 0,
                              SavingThrow.CON: 0, SavingThrow.INT: 0,
                              SavingThrow.WIS: 0,
                              SavingThrow.CHA: 0}
        self.has_pack_tactics = False
        self.has_fanatical_advantage = False
        self.perception = 0
        self.condition = self.State.FINE
        self.conditions = Conditions.NONE
        self.toughness = None
        self.is_dodging = False  # TODO reconcile this somehow with disadvantage_on_incoming_attacks
        self.has_disengaged = False  # TODO Get rid of this
        self.spellslots = None
        self.is_concentrating = False
        self.already_cast_leveled_spell_this_turn = False
        self.shield_spell_active = False
        self.size = Size.MEDIUM
        self.saving_throws_flat_mod = {SavingThrow.STR: [0], SavingThrow.DEX: [0], SavingThrow.CON: [0], SavingThrow.INT: [0], SavingThrow.WIS: [0], SavingThrow.CHA: [0]}
        self.saving_throws_dice_mod = {SavingThrow.STR: [], SavingThrow.DEX: [], SavingThrow.CON: [], SavingThrow.INT: [], SavingThrow.WIS: [], SavingThrow.CHA: []}
        self.saving_throws_roll_mod = {SavingThrow.STR: set(), SavingThrow.DEX: set(), SavingThrow.CON: set(), SavingThrow.INT: set(), SavingThrow.WIS: set(), SavingThrow.CHA: set()}
        self.to_hit_flat_mod = [0]
        self.to_hit_dice_mod = []
        self.action_types_added = []
        self.archetype = CombatantArchetype.MELEE
        self.last_attack_factory_name = None

    def __str__(self):
        return self.name

    def set_round_manager(self, round_manager):
        self.round_manager = round_manager

    def is_alive(self):
        return self.curr_hp > 0

    def roll_initiative(self):
        self.curr_init = random.randint(1, 20) + self.init_bonus

    def add_ability(self, action_type, **kwargs):
        """

        :param action_type: one of Action, BonusAction, Reaction or Passive instances
        :param kwargs: holds the resources that the action_type needs. They are to be stored in this instance. It also holds any information
        that cannot be directly determined by the action_type (such as a level-specific modifier)
        :return: The factory that has been added or None if case of passive actions factories, AoO or errors
        """
        # TODO Consider removing the kwargs and derive everything from the level
        self.action_types_added.append(action_type)
        if isinstance(action_type, Passive):
            match action_type:
                case Passive.MULTIATTACK:
                    try:
                        self.num_attacks = kwargs["num_attacks"]
                        self.curr_num_attacks = kwargs["num_attacks"]
                    except KeyError:
                        logger.error("Arguments incompatible with action type")
                        return
                case Passive.METAMAGIC:
                    self.curr_sorcery_points = kwargs["sorcery_points"]
                    self.max_sorcery_points = kwargs["sorcery_points"]
                case _:
                    pass  # no resources required
            self.passive.append(action_type)
            return None
        elif isinstance(action_type, Action):
            match action_type:
                case Action.MELEE_ATTACK | Action.RANGED_ATTACK | Action.RECKLESS_ATTACK:
                    factory = TO_FACTORY[action_type]
                    self.action_factories.append((action_type, factory(**kwargs, action_type=action_type)))
                    just_added = self.action_factories[-1]
                    self.ammo[just_added[1].name] = just_added[1].ammo
                    return just_added
                case Action.FIREBALL:
                    self.action_factories.append((action_type, TO_FACTORY[action_type](self.dc, Action.FIREBALL, self, has_spell_sculpting=False)))
                    return self.action_factories[-1]
                case Action.FIREBOLT:
                    self.action_factories.append((action_type, TO_FACTORY[action_type](self.spell_to_hit, Action.FIREBOLT, self)))
                    return self.action_factories[-1]
                case Action.CHAOSBOLT:
                    self.action_factories.append((action_type, TO_FACTORY[action_type](self.spell_to_hit, Action.CHAOSBOLT, self)))
                    return self.action_factories[-1]
                case Action.HASTE:
                    self.action_factories.append((action_type, TO_FACTORY[action_type](Action.HASTE, self, self.effect_tracker)))
                    return self.action_factories[-1]
                case Action.DISENGAGE:
                    self.action_factories.append((action_type, TO_FACTORY[action_type](self, action_type)))
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
                    return just_added
                case BonusAction.PAM_BONUS_ATTACK:
                    self.bonus_action_factories.append((action_type, TO_FACTORY[action_type](**kwargs, action_type=action_type)))
                    self.pam_factory = self.bonus_action_factories[-1]
                    return self.bonus_action_factories[-1]
                case BonusAction.RAGE:
                    self.max_rage_uses = RageFactory.get_rage_uses(self.level)
                    self.curr_rage_uses = RageFactory.get_rage_uses(self.level)
                    self.bonus_action_factories.append((action_type, TO_FACTORY[action_type](self)))
                    return self.bonus_action_factories[-1]
                case BonusAction.TOTEM_RAGE:
                    self.max_rage_uses = RageFactory.get_rage_uses(self.level)
                    self.curr_rage_uses = RageFactory.get_rage_uses(self.level)
                    self.bonus_action_factories.append((action_type, TO_FACTORY[action_type](self)))
                    return self.bonus_action_factories[-1]
                case BonusAction.MISTY_STEP:
                    self.bonus_action_factories.append((action_type, TO_FACTORY[action_type](self)))
                    return self.bonus_action_factories[-1]
                case BonusAction.CUNNING_DODGE:
                    self.bonus_action_factories.append((action_type, TO_FACTORY[action_type])) # TODO
                    return self.bonus_action_factories[-1]
                case BonusAction.CUNNING_DISENGAGE:
                    self.bonus_action_factories.append((action_type, TO_FACTORY[action_type](self, action_type))) # TODO
                    return self.bonus_action_factories[-1]
                case BonusAction.CUNNING_HIDE:
                    self.bonus_action_factories.append((action_type, TO_FACTORY[action_type])) # TODO
                    return self.bonus_action_factories[-1]
                case BonusAction.QUICKENED_FIREBALL:
                    self.bonus_action_factories.append((action_type, TO_FACTORY[action_type](self.dc, Action.FIREBALL, self, has_spell_sculpting=False)))
                    return self.bonus_action_factories[-1]
                case BonusAction.QUICKENED_FIREBOLT:
                    self.bonus_action_factories.append((action_type, TO_FACTORY[action_type](self.spell_to_hit, self.level, Action.FIREBOLT, self)))
                    return self.bonus_action_factories[-1]
                case BonusAction.QUICKENED_CHAOSBOLT:
                    self.bonus_action_factories.append((action_type, TO_FACTORY[action_type](self.spell_to_hit, Action.CHAOSBOLT, self)))
                    return self.bonus_action_factories[-1]
                case BonusAction.QUICKENED_HASTE:
                    self.bonus_action_factories.append((action_type, TO_FACTORY[action_type](Action.HASTE, self, self.effect_tracker)))
                    return self.bonus_action_factories[-1]
                case _:
                    pass  # no resources required
        elif isinstance(action_type, Reaction):
            match action_type:
                case Reaction.REACTION_ATTACK:
                    self.reaction_factories.append((action_type, TO_FACTORY[action_type](**kwargs, action_type=action_type)))
                    self.aoo_factory = self.reaction_factories[-1]
                    self.danger_zone_attack = self.reaction_factories[-1]  # By default this is set to the reaction attack
                    self.melee_reaction_range = self.aoo_factory[1].range
                    return None
                case Reaction.SHIELD:
                    self.reaction_factories.append((action_type, TO_FACTORY[action_type](self)))
                    return self.reaction_factories[-1]
                case _:
                    logger.error("Unknown reaction")
                    return None
        elif isinstance(action_type, HasteAction):
            for action in self.action_factories:
                try:
                    # A combatant can have multiple attacks, we need a hastened version of all of them
                    hasted_action = TO_HASTED[action]
                    self.haste_action_factories.append((hasted_action, copy.deepcopy(action))) # Need a copy to change the action_type
                    self.haste_action_factories[-1].action_type = action_type
                    return None
                except KeyError:
                    pass
            return None
        # elif isinstance(action_type, FreeAction):
        #     match action_type:
        #         case FreeAction.RECKLESS_ATTACK:
        #             self.reckless_attack_active = False
        #         case _:
        #             logger.error("Unknown free action")
        #             return
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
        else:
            logger.error("Unknown high level action class")
            return None

    def commit_abilities(self):
        """
        Checks some sanity rules for abilites, e.g. if you have TWIN_SPELL and some spells then you also expect to have their
        """
        # TODO Do I need this or not?
        pass

    def has_passive(self, ability):
        return ability in self.passive

    def receive_dmg(self, dmg, dmg_type):
        """
        Inflicts damage to the combatant
        :param dmg: dmg to be received
        :param dmg_type: dmg type
        :return: actual dmg received accounting for resistances
        """
        if dmg_type in self.resistances:
            dmg = math.floor(dmg / 2)
            logger.info(f"{self.name} is resistant to {dmg_type} and reduced the damage to {dmg}")
        self.curr_hp -= dmg
        if self.curr_hp <= self.max_hp // 3:
            self.condition = self.State.NEAR_DEATH
        elif self.curr_hp <= self.max_hp // 2:
            self.condition = self.State.BLOODIED
        return dmg

    def is_resistant_to(self, dmg_type):
        return dmg_type in self.resistances

    def apply_condition(self, condition):
        self.conditions |= condition

    def remove_condition(self, condition):
        self.conditions ^= condition

    def is_affected_by(self, condition):
        return condition in self.conditions

    def is_affected_by_any(self, *args):
        for condition in args:
            if condition in self.conditions:
                return True
        return False

    def new_turn(self):
        self.has_action = True
        self.has_bonus_action = True
        self.has_reaction = True
        self.curr_num_attacks = self.num_attacks
        self.movement = self.speed
        self.target_position_cache = None  # This has to be reset every turn as the path can be blocked by other combatants
        # if self.is_dodging:
        #     self.saving_throws_roll_mod[SavingThrow.DEX].add(RollModifier.STRAIGHT)
        # self.is_dodging = False # TODO make sure the effect tracker takes care of this
        self.already_cast_leveled_spell_this_turn = False
        if self.shield_spell_active:
            self.ac -= 5
        self.shield_spell_active = False
        self.has_haste_action = False
        self.last_attack_factory_name = None
        self.attack_fsm.set_state('0')

    def reset(self):
        self.has_action = True
        self.has_bonus_action = True
        self.has_reaction = True
        self.curr_num_attacks = self.num_attacks
        self.curr_hp = self.max_hp
        self.target_position_cache = None
        self.movement = self.speed
        self.is_dodging = False
        if self.spellslots:
            self.spellslots.reset()
        self.already_cast_leveled_spell_this_turn = False
        if self.shield_spell_active:
            self.ac -= 5
        self.shield_spell_active = False
        self.conditions = Conditions.NONE
        self.condition = self.State.FINE
        self.has_haste_action = False
        self.saving_throws_flat_mod = dict.fromkeys(self.saving_throws_flat_mod.keys(), 0)
        self.saving_throws_dice_mod = dict.fromkeys(self.saving_throws_dice_mod.keys(), [])
        self.saving_throws_roll_mod = dict.fromkeys(self.saving_throws_roll_mod.keys(), set())
        for f in self.action_factories:
            if FactoryFlags.HAS_AMMO in f[1].flags:
                self.ammo[f[1].name] = f[1].ammo
        for f in self.bonus_action_factories:
            if FactoryFlags.HAS_AMMO in f[1].flags:
                self.ammo[f[1].name] = f[1].ammo
        self.last_attack_factory_name = None


    # @abstractmethod
    # def calculate_threat(self, battle_map):
    #     """
    #     Calculates the threat potential of the combatant for all their abilities
    #     @param battle_map:
    #     @return:
    #     """
    #     return 0
    #
    #
    # def calculate_threat_approx(self, battle_map):
    #     """
    #     Calculates the threat potential of the combatant as a non-self character (i.e. being considered as a target)
    #     @param battle_map:
    #     @return:
    #     """
    #     # iterate over abilities, calculate their approx threat and order them and return the max
    #     return 0
    #
    # def calculate_threat_approx_haste_action(self, battle_map):
    #     """
    #     Calculates the threat potential of the combatant as a non-self character that can be achieved with a haste action
    #     @param battle_map:
    #     @return:
    #     """
    #     return 0

    def is_bloodied_or_worse(self):
        return self.condition.value >= self.State.BLOODIED.value

    def is_near_death(self):
        return self.condition is self.State.NEAR_DEATH

    def add_team(self, team_color):
        self.team_color = team_color

    @abstractmethod
    def prompt_aoo(self, moving_combatant):
        return None

    def prompt_pam(self, moving_combatant):
        return None

    def prompt_attack_reaction(self, attacking_combatant, attack_roll):
        return None

    def prompt_dmg_reaction(self, attacking_combatant, dmg, dmg_type):
        return None

    def prompt_after_hit_reaction(self, attacking_combatant, attack_roll):
        return None
