import copy

import logging
import random
import math
from contextlib import contextmanager

from simulator.actions.actoid import FactoryFlags
from simulator.actions.default_action_plan_strategy import DefaultActionPlanStrategy
from simulator.effects.action_enabler_effect import ActionEnablerEffect
from simulator.misc import SavingThrow, Conditions, Size, CombatantArchetype, ConditionWithDC
from enum import Enum
from abc import ABC, abstractmethod
from simulator.actions.dodge import DodgeFactory
from simulator.actions.disengage import DisengageFactory
from simulator.abilities.rage import RageFactory
from simulator.actions.action_constants import TO_FACTORY, TO_HASTED, TO_QUICKENED, TO_TWINNED
from simulator.actions.action_types import Passive, Action, BonusAction, Reaction, HasteAction, MetaAction
from simulator.proto_combatant import ProtoCombatant

logger = logging.getLogger("EncounTroll")


class Combatant(ABC, ProtoCombatant):

    def __init__(self, effect_tracker, name, level, hp, ac, init_bonus, spell_to_hit, speed, resistances, dc):
        self.effect_tracker = effect_tracker
        self.name = name
        self.level = level
        self.action_factories = [(Action.DODGE, DodgeFactory(self)), (Action.DISENGAGE, DisengageFactory(Action.DISENGAGE, self))]
        self.dodge_factory = self.action_factories[0]
        self.disengage_factory = self.action_factories[1]
        self.bonus_action_factories = []
        self.reaction_factories = []
        self.danger_zone_attack = None
        self.haste_action_factories = []
        self.action_plan_strategy = DefaultActionPlanStrategy(self)
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
        self.speed = speed / 5
        self.movement = speed / 5
        self.ammo = {}  # Dict of type Attack Factory Name -> current ammo
        self.resistances = resistances
        self.multiattack_in_progress = False
        self.attack_fsm = None
        self.action_fsm = None
        self.action_plan = None
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
        self.athletics = 0
        self.acrobatics = 0
        self.has_pack_tactics = False
        self.perception = 0
        self.conditions = Conditions.NONE
        self.dc_conditions = []
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
        self.shortest_paths_cache = None

    def __str__(self):
        return self.name

    def get_current_form(self):
        return self

    def get_original_form(self):
        return self

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
                case Passive.METAMAGIC:
                    self.curr_sorcery_points = kwargs["sorcery_points"]
                    self.max_sorcery_points = kwargs["sorcery_points"]
                case Passive.PACK_TACTICS:
                    self.has_pack_tactics = True
                case Passive.FANATIC_ADVANTAGE:
                    self.already_used_fanatic_advantage = False
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
                case Action.BITE_WITH_SWALLOW:
                    factory = TO_FACTORY[action_type]
                    self.action_factories.append((action_type, factory(**kwargs, action_type=action_type)))
                    just_added = self.action_factories[-1]
                    self.ammo[just_added[1].name] = just_added[1].ammo
                    self.is_constricting = False
                    return just_added
                case Action.FIREBALL:
                    self.action_factories.append(
                        (action_type, TO_FACTORY[action_type](self.dc, Action.FIREBALL, self, has_spell_sculpting=False)))
                    return self.action_factories[-1]
                case Action.FIREBOLT:
                    self.action_factories.append(
                        (action_type, TO_FACTORY[action_type](self.spell_to_hit, Action.FIREBOLT, self)))
                    return self.action_factories[-1]
                case Action.CHAOSBOLT:
                    self.action_factories.append(
                        (action_type, TO_FACTORY[action_type](self.spell_to_hit, Action.CHAOSBOLT, self)))
                    return self.action_factories[-1]
                case Action.SCORCHING_RAY:
                    self.action_factories.append(
                        (action_type, TO_FACTORY[action_type](self.spell_to_hit, Action.SCORCHING_RAY, self)))
                    return self.action_factories[-1]
                case Action.HASTE:
                    self.action_factories.append(
                        (action_type, TO_FACTORY[action_type](Action.HASTE, self, self.effect_tracker)))
                    return self.action_factories[-1]
                case Action.DISENGAGE:
                    self.action_factories.append((action_type, TO_FACTORY[action_type](action_type, self)))
                    return self.action_factories[-1]
                case Action.WILDSHAPE:
                    self.max_wildshape_uses = TO_FACTORY[action_type].get_wildshape_uses(self.level)
                    self.curr_wildshape_uses = TO_FACTORY[action_type].get_wildshape_uses(self.level)
                    self.current_wildshape_form = None
                    self.bonus_action_factories.append((action_type, TO_FACTORY[action_type](self)))
                    def wildshape_get(self):
                        return self if self.current_wildshape_form is None else self.current_wildshape_form
                    self.get_current_form = wildshape_get.__get__(self, Combatant)
                    return self.bonus_action_factories[-1]
                case Action.POUNCE:
                    factory = TO_FACTORY[action_type]
                    self.action_factories.append((action_type, factory(**kwargs)))
                    return self.action_factories[-1]
                case Action.CONSTRICT:
                    factory = TO_FACTORY[action_type]
                    self.is_constricting = False
                    self.action_factories.append((action_type, factory(**kwargs)))
                    return self.action_factories[-1]
                case Action.FLAMING_SPHERE:
                    self.action_factories.append((action_type, TO_FACTORY[action_type](action_type, self.dc, self)))
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
                    self.bonus_action_factories.append((action_type, TO_FACTORY[action_type]))  # TODO
                    return self.bonus_action_factories[-1]
                case BonusAction.CUNNING_DISENGAGE:
                    self.bonus_action_factories.append((action_type, TO_FACTORY[action_type](action_type, self)))  # TODO
                    return self.bonus_action_factories[-1]
                case BonusAction.CUNNING_HIDE:
                    self.bonus_action_factories.append((action_type, TO_FACTORY[action_type]))  # TODO
                    return self.bonus_action_factories[-1]
                case BonusAction.QUICKENED_FIREBALL:
                    self.bonus_action_factories.append(
                        (action_type, TO_FACTORY[action_type](self.dc, Action.FIREBALL, self, has_spell_sculpting=False)))
                    return self.bonus_action_factories[-1]
                case BonusAction.QUICKENED_FIREBOLT:
                    self.bonus_action_factories.append(
                        (action_type, TO_FACTORY[action_type](self.spell_to_hit, self.level, Action.FIREBOLT, self)))
                    return self.bonus_action_factories[-1]
                case BonusAction.QUICKENED_CHAOSBOLT:
                    self.bonus_action_factories.append(
                        (action_type, TO_FACTORY[action_type](self.spell_to_hit, Action.CHAOSBOLT, self)))
                    return self.bonus_action_factories[-1]
                case BonusAction.QUICKENED_HASTE:
                    self.bonus_action_factories.append(
                        (action_type, TO_FACTORY[action_type](Action.HASTE, self, self.effect_tracker)))
                    return self.bonus_action_factories[-1]
                case BonusAction.MOON_WILDSHAPE:
                    self.max_wildshape_uses = TO_FACTORY[action_type].get_wildshape_uses(self.level)
                    self.curr_wildshape_uses = TO_FACTORY[action_type].get_wildshape_uses(self.level)
                    self.current_wildshape_form = None
                    self.bonus_action_factories.append((action_type, TO_FACTORY[action_type](self, action_type)))
                    def wildshape_get(self):
                        return self if self.current_wildshape_form is None else self.current_wildshape_form
                    self.get_current_form = wildshape_get.__get__(self, Combatant)
                    return self.bonus_action_factories[-1]
                case _:
                    pass  # no resources required
        elif isinstance(action_type, Reaction):
            match action_type:
                case Reaction.REACTION_ATTACK | Reaction.BITE_WITH_SWALLOW_REACTION:
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

    def receive_dmg(self, dmg, dmg_type):
        """
        Inflicts damage to the combatant
        :param dmg: dmg to be received
        :param dmg_type: dmg type
        :return: actual dmg received accounting for resistances
        """
        # TODO Redo this into lists of dmg and dmg types for compound dmg attacks. Also has to support knocking out of wildshape
        if dmg_type in self.resistances:
            dmg = math.floor(dmg / 2)
            logger.info(f"{self.name} is resistant to {dmg_type} and reduced the damage to {dmg}")
        self.curr_hp -= dmg
        if self.curr_hp <= 0 and self.get_original_form() is not self:
            self.get_original_form().curr_hp += self.curr_hp  # carry-over damage
            self.effect_tracker.deactivate_wildshape(self.get_original_form())
        return dmg

    def is_resistant_to(self, dmg_type):
        return dmg_type in self.resistances

    def apply_condition(self, condition: Conditions):
        self.conditions |= condition

    def remove_condition(self, condition: Conditions):
        self.conditions ^= condition

    def is_affected_by(self, condition: Conditions):
        for dc_cond in self.dc_conditions:
            if condition in dc_cond.conditions:
                return True
        return condition in self.conditions

    def needs_to_break_out_of_grapple(self):
        for dc_cond in self.dc_conditions:
            if Conditions.GRAPPLED in dc_cond.conditions and dc_cond.needs_action_to_break:
                return dc_cond
        return None

    def is_affected_by_any(self, *args):
        for condition in args:
            for dc_cond in self.dc_conditions:
                if condition in dc_cond.conditions:
                    return True
            if condition in self.conditions:
                return True
        return False

    def apply_dc_condition(self, condition: ConditionWithDC):
        self.dc_conditions.append(condition)

    def remove_dc_condition(self, condition: ConditionWithDC):
        self.dc_conditions.remove(condition)

    def new_turn(self):
        self.has_action = True
        self.has_bonus_action = True
        self.has_reaction = True
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
        self.action_plan = None

    def reset(self):
        self.has_action = True
        self.has_bonus_action = True
        self.has_reaction = True
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
        self.conditions = []
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

    @contextmanager
    def as_if_used_action_enabler(self, action, battle_map):
        if isinstance(action, ActionEnablerEffect):
            try:
                action.enable(battle_map)
                yield True
            finally:
                action.disable(battle_map)
        else:
            yield False

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


    def calculate_action_plan(self, battle_map, distances, shortest_paths):
        """
        A thin wrapper for the calculation of action plan
        :param battle_map:
        :param distances: the distances to all squares (result of Dijkstra)
        :param shortest_paths: the shortest paths to all squares (result of Dijkstra)
        :return: the action plan
        """
        return self.action_plan_strategy.calculate_action_plan(battle_map, distances, shortest_paths)