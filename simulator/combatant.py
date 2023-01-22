import random
import math
from simulator.misc import SavingThrow, Conditions, RollModifier, Size
from simulator.action_factory import *
from enum import Enum
from abc import ABC, abstractmethod
from simulator.abilities.totem_rage import TotemRageFactory

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

    def __init__(self, name, level, hp, ac, init_bonus, spell_to_hit, speed, resistances, dc):
        self.name = name
        self.level = level
        self.actions = [Action.ATTACK, Action.DODGE]
        self.bonus_actions = []
        self.reactions = [Reaction.REACTION_ATTACK]
        self.haste_actions = []
        self.passive = []
        self.max_hp = hp
        self.curr_hp = hp
        self.ac = ac
        self.dc = dc
        self.init_bonus = init_bonus
        self.spell_to_hit = spell_to_hit
        self.attacks = []
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
        self.resistances = resistances
        self.multiattack_in_progress = False
        self.team_color = ""
        self.selected_target = None
        self.planned_movement = None
        self.movement_generator = None
        self.max_melee_range = 1
        self.target_position_cache = None
        self.action_resolver = None
        self.disadvantage_on_incoming_attacks = False
        # maps saving_throw_type -> (bonus, RollModifier)
        self.saving_throws = {SavingThrow.STR: [0, RollModifier.STRAIGHT], SavingThrow.DEX: [0, RollModifier.STRAIGHT],
                              SavingThrow.CON: [0, RollModifier.STRAIGHT], SavingThrow.INT: [0, RollModifier.STRAIGHT],
                              SavingThrow.WIS: [0, RollModifier.STRAIGHT],
                              SavingThrow.CHA: [0, RollModifier.STRAIGHT]}
        self.has_pack_tactics = False
        self.has_fanatical_advantage = False
        self.perception = 0
        self.condition = self.State.FINE
        self.conditions = Conditions.NONE
        self.toughness = None
        self.is_dodging = False  # TODO reconcile this somehow with disadvantage_on_incoming_attacks
        self.spellslots = None
        self.is_concentrating = False
        self.already_cast_leveled_spell_this_turn = False
        self.shield_spell_active = False
        self.size = Size.MEDIUM
        self.saving_throws_flat_mod = {SavingThrow.STR: [0], SavingThrow.DEX: [0], SavingThrow.CON: [0], SavingThrow.INT: [0], SavingThrow.WIS: [0], SavingThrow.CHA: [0]}
        self.saving_throws_dice_mod = {SavingThrow.STR: [], SavingThrow.DEX: [], SavingThrow.CON: [], SavingThrow.INT: [], SavingThrow.WIS: [], SavingThrow.CHA: []}
        self.to_hit_flat_mod = [0]
        self.to_hit_dice_mod = []

    def __str__(self):
        return self.name

    def set_round_manager(self, round_manager):
        self.round_manager = round_manager

    def is_alive(self):
        return self.curr_hp > 0

    def roll_initiative(self):
        self.curr_init = random.randint(1, 20) + self.init_bonus

    def add_ability(self, action_type, **kwargs):
        # TODO This should also give combatants factories now
        """

        :param action_type: one of Action, BonusAction, Reaction or Passive instances
        :param kwargs: holds the resources that the action_type needs. They are to be stored in this instance. It also holds any information
        that cannot be directly determined by the action_type (such as a level-specific modifier)
        :return: nothing
        """
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
        elif isinstance(action_type, Action):
            self.actions.append(action_type)
        elif isinstance(action_type, BonusAction):
            match action_type:
                case BonusAction.RAGE | BonusAction.TOTEM_RAGE:
                    self.max_rage_uses = TotemRageFactory.get_rage_uses(self.level)
                    self.curr_rage_uses = TotemRageFactory.get_rage_uses(self.level)
                    self.rage_active = False
                case _:
                    pass  # no resources required
            self.bonus_actions.append(action_type)
        elif isinstance(action_type, Reaction):
            self.reactions.append(action_type)
        elif isinstance(action_type, FreeAction):
            match action_type:
                case FreeAction.RECKLESS_ATTACK:
                    self.reckless_attack_active = False
                case _:
                    logger.error("Unknown free action")
        elif isinstance(action_type, MetaAction):
            match action_type:
                case MetaAction.QUICKENED_SPELL | MetaAction.EMPOWERED_SPELL | MetaAction.TWINNED_SPELL:
                    assert Passive.METAMAGIC in self.passive
        else:
            logger.error("Unknown high level action class")

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
            logger.debug(f"{self.name} is resistant to {dmg_type} and reduced the damage to {dmg}")
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
        if self.is_dodging:
            self.saving_throws[SavingThrow.DEX][1] = RollModifier.STRAIGHT
        self.is_dodging = False
        self.already_cast_leveled_spell_this_turn = False
        if self.shield_spell_active:
            self.ac -= 5
        self.shield_spell_active = False
        self.has_haste_action = False

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
        for st in self.saving_throws.values():
            st[1] = RollModifier.STRAIGHT

    @abstractmethod
    def calculate_threat(self, battle_map):
        """
        Calculates the threat potential of the combatant for all their abilities
        @param battle_map:
        @return:
        """
        return 0


    def calculate_threat_approx(self, battle_map):
        """
        Calculates the threat potential of the combatant as a non-self character (i.e. being considered as a target)
        @param battle_map:
        @return:
        """
        # iterate over abilities, calculate their approx threat and order them and return the max
        return 0

    def calculate_threat_approx_haste_action(self, battle_map):
        """
        Calculates the threat potential of the combatant as a non-self character that can be achieved with a haste action
        @param battle_map:
        @return:
        """
        return 0

    def is_bloodied_or_worse(self):
        return self.condition.value >= self.State.BLOODIED.value

    def is_near_death(self):
        return self.condition is self.State.NEAR_DEATH

    def add_team(self, team_color):
        self.team_color = team_color

    @abstractmethod
    def prompt_aoo(self, moving_combatant):
        return None,

    def prompt_pam(self, moving_combatant):
        return None,

    def prompt_attack_reaction(self, attacking_combatant, attack_roll):
        return None,

    def prompt_dmg_reaction(self, attacking_combatant, dmg, dmg_type):
        return None,

    def prompt_after_hit_reaction(self, attacking_combatant):
        return None,
