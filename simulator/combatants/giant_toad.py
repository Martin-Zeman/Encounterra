import copy

import numpy as np

from ..abilities.on_hit_auto_restrained import OnHitAutoRestrained
from ..abilities.on_hit_swallow import OnHitSwallow
from ..actions.action_types import Action, Reaction
from ..battle_map import Map, _get_free_coords_in_cartesian_range
from ..effects.effect import EffectType
from ..utils.state_machine_template import StateMachineTemplate
from ..combatant import Combatant
from ..misc import DamageType, SavingThrow, Size, SkillCheck, Class
from ..conditions import Conditions, remove_all_conditions_of_type
import logging

logger = logging.getLogger("Encounterra")


class GiantToad(Combatant):

    name = "Giant Toad"
    cls = Class.MONSTER.BEAST
    level = 1
    id = Combatant.generate_unique_id(name, cls, level)

    def __init__(self, num_or_name=1):
        super().__init__(num_or_name, hp=39, ac=11, init_bonus=1, spell_to_hit=0, speed=20, resistances=set(), dc=0)
        self.size = Size.LARGE
        self.bite = self.add_ability(Action.PRE_SWALLOW_BITE,  name="Bite", combatant=self, to_hit=4, dmg_dice=((1, 10),), dmg_bonus=2, dmg_type=DamageType.Piercing, attack_range=1, crit_range=1,
                                     on_hit=[OnHitAutoRestrained(SkillCheck.ATHLETICS, 13)], extra_dmg=[((1, 10), DamageType.Poison)])
        self.bite_and_swallow = self.add_ability(Action.BITE_AND_SWALLOW, name="Bite and Swallow", combatant=self, to_hit=4, dmg_dice=((1, 10),), dmg_bonus=2,
                                     dmg_type=DamageType.Piercing, attack_range=1, crit_range=1, on_hit=[OnHitSwallow()], extra_dmg=[((1, 10), DamageType.Poison)])
        self.add_ability(Reaction.REACTION_ATTACK,  name="Bite", combatant=self, to_hit=4, dmg_dice=((1, 10),), dmg_bonus=2, dmg_type=DamageType.Piercing, attack_range=1, crit_range=1,
                         on_hit=[OnHitAutoRestrained(SkillCheck.ATHLETICS, 13)], extra_dmg=[((1, 10), DamageType.Poison)])
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = 2
        self.saving_throws[SavingThrow.DEX] = 2
        self.saving_throws[SavingThrow.CON] = 1
        self.saving_throws[SavingThrow.INT] = -1
        self.saving_throws[SavingThrow.WIS] = 0
        self.saving_throws[SavingThrow.CHA] = -1
        self.athletics = 2
        self.acrobatics = 1
        self.passive_perception = 10

    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_transition(str(self.bite[1]), '0', 'nop')  # Melee
        self.attack_fsm.add_transition(str(self.bite_and_swallow[1]), '0', 'nop')  # Melee

    # def new_turn(self):
    #     super().new_turn()
    #     if self.swallowed_target:
    #         dice = (3, 6)
    #         dmg_dice_sum = roll_dice(dice)
    #         logger.info(f"{self.name} is digesting {self.swallowed_target} for {dmg_dice_sum} dmg", extra={"team": self.team_color})
    #         self.swallowed_target.receive_dmg(dmg_dice_sum, DamageType.Acid)

    def on_die(self):
        if self.swallowed_target:
            logger.info(f"{self.swallowed_target} is spat out and no longer swallowed", extra={"team": self.team_color})
            remove_all_conditions_of_type(self.swallowed_target, Conditions.SWALLOWED)  # This should remove all the accompanying conditions too
            if self.swallowed_target.is_alive():
                battle_map = Map.get()
                battle_map.effect_tracker.remove_effect_from_combatant_by_type(self.swallowed_target, EffectType.DIGESTION)
                free_coords = _get_free_coords_in_cartesian_range(
                    battle_map.grid,
                    battle_map.get_combatant_position(self).get(),
                    inflate_to_dist=self.swallowed_target.size.value,
                    rng=1, combatant_id=self.swallowed_target.id)
                if not free_coords:
                    logger.error("No space around the dead Giant Toad to spit out the swallowed combatant")
                    return
                else:
                    battle_map.set_combatant_coordinates(self.swallowed_target, np.array(next(iter(free_coords))))
            self.swallowed_target = None

    def export_resources(self):
        return {
            'movement': self.movement,
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'has_haste_action': self.has_haste_action,
            'attack_fsm_state': self.attack_fsm.state,
            'swallowed_target': self.swallowed_target,
            'ammo': copy.deepcopy(self.ammo)
        }

    def import_resources(self, resources):
        self.movement = resources['movement']
        self.has_action = resources['has_action']
        self.has_bonus_action = resources['has_bonus_action']
        self.has_haste_action = resources['has_haste_action']
        self.attack_fsm.set_state(resources['attack_fsm_state'])
        self.swallowed_target = resources['swallowed_target']
        self.ammo = resources['ammo']

    def prompt_aoo(self, moving_combatant):
        if self.has_reaction and not self.constricted_target:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self.name} took an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
