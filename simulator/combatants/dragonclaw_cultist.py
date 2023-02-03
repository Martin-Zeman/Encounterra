from simulator.combatant import Combatant
from simulator.actions.movement import MovementGenerator
from simulator.misc import DamageType
from simulator.action_factory import *
from simulator.misc import Side
import logging

logger = logging.getLogger(__name__)


class DragonclawCultist(Combatant):

    def __init__(self, effect_tracker, name="Dragonclaw"):
        super().__init__(effect_tracker, name, level=5, hp=16, ac=14, init_bonus=3, spell_to_hit=0, speed=30, resistances=set(), dc=0)
        self.add_ability(Action.ATTACK,  name="Scimitar", combatant=self, to_hit=5, dmg_dice="1d6", dmg_bonus=3, dmg_type=DamageType.Slashing, attack_range=1, crit_range=[20], attack_type=AttackFactory.Type.MELEE)
        self.add_ability(Reaction.REACTION_ATTACK,  name="Scimitar", combatant=self, to_hit=5, dmg_dice="1d6", dmg_bonus=3, dmg_type=DamageType.Slashing, attack_range=1, crit_range=[20], attack_type=AttackFactory.Type.MELEE)
        self.add_ability(Passive.MULTIATTACK, num_attacks=2)
        self.max_melee_range = 1  # TODO: maybe add a lookup here
        self.has_pack_tactics = True
        self.has_fanatical_advantage = True

    def attack_routine(self, battle_map):
        if battle_map.are_in_range(self, self.selected_target, self.max_melee_range):
            logger.debug("Is in range")
            if self.has_action and self.curr_num_attacks and not self.multiattack_in_progress:
                self.multiattack_in_progress = True
            if self.curr_num_attacks and self.multiattack_in_progress:
                attack_args = self.attack_args[Action.ATTACK]
                attack_args[2] = self.selected_target  # sets the target
                logger.debug(f"{self.name} uses action {attack_args[0]} against {self.selected_target}",
                             extra={"team": self.team_color})
                return (self.actions[0], *attack_args)
            else:
                self.multiattack_in_progress = False
        else:
            logger.debug("Is out of range")
            return (MetaAction.DONE,)

    def get_action(self, battle_map):
        while self.has_action or self.movement or self.has_haste_action:
            # logger.debug(f"Has action {self.has_action}, movement {self.movement}")

            dist = None
            if self.selected_enemy is None or not self.selected_enemy.is_alive():
                # Get new target
                self.selected_target, dist = battle_map.get_nearest(self, Side.ENEMY)
                if not self.selected_target:
                    return (MetaAction.DONE,)

            target_position = battle_map.get_combatant_position(self.selected_target)
            logger.debug(f"Target is at {target_position}")
            if not dist:
                dist = battle_map.get_hop_distance(self, self.selected_target)
            if self.movement and self.has_action and dist > 1:
                # I haven't attacked yet and I'm too far away, move into range
                path = battle_map.get_path_to(self, self.selected_target)
                if not path:
                    logger.debug(f"{self.name} has nowhere to go and uses the dodge action", extra={"team": self.team_color})
                    return (Action.DODGE,)
                self.movement_generator = MovementGenerator(self, path, True).get_generator()
                try:
                    movement = next(self.movement_generator)
                    logger.debug("Moving")
                    return (Movement.STANDARD, movement)
                except StopIteration:
                    pass  # can't go any farther
            elif (self.has_action or self.multiattack_in_progress) and dist <= 1:
                # if I'm in range and I still have an action then attack
                attack = self.attack_routine(battle_map)
                if attack:
                    return attack
            if self.has_action:
                logger.debug(f"{self.name} uses the dodge action", extra={"team": self.team_color})
                return (Action.DODGE,)
            return (MetaAction.DONE,)
        return (MetaAction.DONE,)

    def prompt_aoo(self, moving_combatant):
        # only use it if I go before my selected target in initiative so that I can move away and use sentinel+pam
        if self.has_reaction:
            aoo = self.aoo_factory(moving_combatant)
            logger.debug(f"{self.name} took an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
