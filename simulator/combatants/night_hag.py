import math

from ..actions.action_types import Action, Reaction, Passive
from ..resources import Uses, ResourceRefreshType
from ..utils.state_machine_template import StateMachineTemplate
from ..combatant import Combatant
from ..misc import DamageType, SavingThrow, Class, SpellcastingResourceType
import logging

logger = logging.getLogger("Encounterra")


class NightHag(Combatant):

    type = "Night Hag"

    def __init__(self, num_or_name=1):
        super().__init__(num_or_name, Class.MONSTER.FIEND, level=5, hp=112, ac=17, init_bonus=2, speed=30, spell_to_hit=6, resistances={DamageType.Fire, DamageType.Cold, DamageType.Bludgeoning, DamageType.Slashing, DamageType.Piercing}, dc=14)
        self.claws = self.add_ability(Action.MELEE_ATTACK, name="Claws", combatant=self, to_hit=7, dmg_dice="2d8", dmg_bonus=4,
                         dmg_type=DamageType.Slashing, attack_range=1)
        self.add_ability(Reaction.REACTION_ATTACK, name="Claws", combatant=self, to_hit=7, dmg_dice="2d8", dmg_bonus=4,
                         dmg_type=DamageType.Slashing, attack_range=1)
        ray_of_enfeeblement_two_uses = Uses(2, ResourceRefreshType.LONG_REST)
        sleep_two_uses = Uses(2, ResourceRefreshType.LONG_REST)
        inf_uses = Uses(math.inf, ResourceRefreshType.LONG_REST)
        self.resources.append(ray_of_enfeeblement_two_uses)
        self.resources.append(sleep_two_uses)
        self.resources.append(inf_uses)
        self.add_ability(Passive.SPELLCASTING, resource_type=SpellcastingResourceType.SPECIAL)
        self.add_ability(Passive.MAGIC_RESISTANCE)
        self.add_ability(Action.MAGIC_MISSILE, resource=inf_uses)
        self.add_ability(Action.RAY_OF_ENFEEBLEMENT, resource=ray_of_enfeeblement_two_uses)
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = 4
        self.saving_throws[SavingThrow.DEX] = 2
        self.saving_throws[SavingThrow.CON] = 3
        self.saving_throws[SavingThrow.INT] = 3
        self.saving_throws[SavingThrow.WIS] = 2
        self.saving_throws[SavingThrow.CHA] = 3
        self.athletics = 4
        self.acrobatics = 2
        self.passive_perception = 16

    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_transition(str(self.claws[1]), '0', 'nop')

    def prompt_aoo(self, moving_combatant):
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self.name} took an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None

    def export_resources(self):
        return {
            'movement': self.movement,
            'resources': [r.export_resource() for r in self.resources],
            'cast_leveled_spell': self.already_cast_leveled_spell_this_turn,
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'has_haste_action': self.has_haste_action,
            'attack_state_machine': self.attack_fsm.state
        }

    def import_resources(self, resources):
        self.movement = resources['movement']
        for idx, r in enumerate(resources['resources']):
            self.resources[idx].import_resource(uses=r)
        self.already_cast_leveled_spell_this_turn = resources['cast_leveled_spell']
        self.has_action = resources['has_action']
        self.has_bonus_action = resources['has_bonus_action']
        self.has_haste_action = resources['has_haste_action']
        self.attack_fsm.set_state(resources['attack_state_machine'])
