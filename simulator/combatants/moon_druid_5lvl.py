import copy
from functools import cache

from simulator.abilities.wildshape import WildshapeFactory
from simulator.actions.action_types import Action, Reaction, BonusAction
from simulator.actions.moon_druid_action_plan_strategy import MoonDruidActionPlanStrategy
from simulator.utils.state_machine_template import StateMachineTemplate
from simulator.combatant import Combatant
from simulator.spellslots import Spellslots, Class
from simulator.misc import CombatantArchetype, DamageType, SavingThrow
import logging

logger = logging.getLogger("EncounTroll")


class MoonDruid5Lvl(Combatant):

    def __init__(self, name="MoonDruid5Lvl"):
        super().__init__(name, level=5, hp=42, ac=15, init_bonus=1, speed=35, spell_to_hit=7, resistances=set(), dc=15)
        self.scimitar = self.add_ability(Action.MELEE_ATTACK, name="Scimitar", combatant=self, to_hit=4, dmg_dice="1d6", dmg_bonus=1, dmg_type=DamageType.Slashing, attack_range=1)
        self.add_ability(Reaction.REACTION_ATTACK, name="Scimitar", combatant=self, to_hit=4, dmg_dice="1d6", dmg_bonus=1, dmg_type=DamageType.Slashing, attack_range=1)
        self.add_ability(Action.FLAMING_SPHERE)
        self.longbow = self.add_ability(Action.RANGED_ATTACK, name="Longbow", combatant=self, to_hit=4, dmg_dice="1d8", dmg_bonus=1, dmg_type=DamageType.Piercing, attack_range=120)
        self.danger_zone_attack = self.scimitar
        self.wildshape_factory = self.add_ability(BonusAction.MOON_WILDSHAPE)
        self.action_plan_strategy = MoonDruidActionPlanStrategy(self)
        self.build_attack_fms()
        self.spellslots = Spellslots(Class.DRUID, self.level)
        self.archetype = CombatantArchetype.RANGED
        self.saving_throws[SavingThrow.STR] = -1
        self.saving_throws[SavingThrow.DEX] = 1
        self.saving_throws[SavingThrow.CON] = 3
        self.saving_throws[SavingThrow.INT] = 4
        self.saving_throws[SavingThrow.WIS] = 7
        self.saving_throws[SavingThrow.CHA] = 1
        self.athletics = 2
        self.acrobatics = 1

    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_transition(str(self.scimitar[1]), '0', 'nop')
        self.attack_fsm.add_transition(str(self.longbow[1]), '0', 'nop')


    def new_turn(self):
        super().new_turn()
        self.action_plan_strategy.best_wildshape_plan_data = None
        if self.current_wildshape_form is not None:
            self.current_wildshape_form.new_turn()

    def reset(self):
        super().reset()
        self.curr_wildshape_uses = self.max_wildshape_uses

    def prompt_aoo(self, moving_combatant):
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self.name} took an AoO {aoo} against {moving_combatant}",
                        extra={"team": self.team_color})
            return aoo
        return None

    def export_resources(self):
        return {
            'spellslots': copy.deepcopy(self.spellslots),
            'cast_leveled_spell': self.already_cast_leveled_spell_this_turn,
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'has_haste_action': self.has_haste_action,
            'attack_state_machine': self.attack_fsm.state,
            'curr_wildshape_uses':  self.curr_wildshape_uses
        }

    def load_resources(self, resources):
        self.spellslots = resources['spellslots']
        self.already_cast_leveled_spell_this_turn = resources['cast_leveled_spell']
        self.has_action = resources['has_action']
        self.has_bonus_action = resources['has_bonus_action']
        self.has_haste_action = resources['has_haste_action']
        self.attack_fsm.set_state(resources['attack_state_machine'])
        self.curr_wildshape_uses = resources['curr_wildshape_uses']

    @cache
    def get_dijkstra_from_cache(self):
        sizes = WildshapeFactory.get_wildshape_form_sizes(self.level, BonusAction.MOON_WILDSHAPE)

