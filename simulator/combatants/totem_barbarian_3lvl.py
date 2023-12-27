from ..actions.action_types import Action, Reaction, BonusAction, Passive
from ..utils.state_machine_template import StateMachineTemplate
from ..combatant import Combatant
from ..misc import DamageType, SavingThrow, Class
import logging

logger = logging.getLogger("Encounterra")


class TotemBarbarian5Lvl(Combatant):

    name = "Totem Barbarian 5. Level"
    cls = Class.BARBARIAN.PATH_OF_THE_TOTEM_WARRIOR
    level = 3
    id = Combatant.generate_unique_id(name, cls, level)

    def __init__(self, num_or_name=1):
        super().__init__(num_or_name, hp=35, ac=14, init_bonus=1, spell_to_hit=0, speed=30, resistances=set(), dc=13)
        self.axe = self.add_ability(Action.MELEE_ATTACK,  name="Two-handed axe", combatant=self, to_hit=5, dmg_dice="1d12", dmg_bonus=3, dmg_type=DamageType.Slashing, attack_range=1)
        self.javelin_attack = self.add_ability(Action.RANGED_ATTACK, name="Javelin", combatant=self, to_hit=5, dmg_dice="1d6", dmg_bonus=3, dmg_type=DamageType.Piercing, attack_range=24, crit_range=1, uses_dex=False)
        self.add_ability(Reaction.REACTION_ATTACK,  name="Two-handed axe", combatant=self, to_hit=5, dmg_dice="1d12", dmg_bonus=3, dmg_type=DamageType.Slashing, attack_range=1)
        self.add_ability(BonusAction.TOTEM_RAGE)
        self.add_ability(Passive.DANGER_SENSE)
        self.axe_recklessly = self.add_ability(Action.RECKLESS_ATTACK, name="Two-handed axe recklessly", combatant=self, to_hit=7, dmg_dice="1d12", dmg_bonus=4, dmg_type=DamageType.Slashing, attack_range=1)
        self.build_attack_fms()
        self.saving_throws[SavingThrow.STR] = 5
        self.saving_throws[SavingThrow.DEX] = 1
        self.saving_throws[SavingThrow.CON] = 5
        self.saving_throws[SavingThrow.INT] = 1
        self.saving_throws[SavingThrow.WIS] = 0
        self.saving_throws[SavingThrow.CHA] = 1
        self.athletics = 5
        self.acrobatics = 1
        self.passive_perception = 10


    def build_attack_fms(self):
        self.attack_fsm = StateMachineTemplate()
        self.attack_fsm.add_transition(str(self.axe[1]), '0', 'nop')  # Melee
        self.attack_fsm.add_transition(str(self.axe_recklessly[1]), '0', 'nop')
        self.attack_fsm.add_transition(str(self.javelin_attack[1]), '0', 'nop')

    def export_resources(self):
        return {
            'movement': self.movement,
            'has_action': self.has_action,
            'has_bonus_action': self.has_bonus_action,
            'curr_rage_uses': self.curr_rage_uses,
            'has_haste_action': self.has_haste_action,
            'attack_fsm_state': self.attack_fsm.state
        }

    def import_resources(self, resources):
        self.movement = resources['movement']
        self.has_action = resources['has_action']
        self.has_bonus_action = resources['has_bonus_action']
        self.has_haste_action = resources['has_haste_action']
        self.curr_rage_uses = resources['curr_rage_uses']
        self.attack_fsm.state = resources['attack_fsm_state']

    def prompt_aoo(self, moving_combatant):
        if self.has_reaction:
            aoo = self.aoo_factory[1].create(moving_combatant)
            logger.info(f"{self} taken an AoO {aoo} against {moving_combatant}",
                         extra={"team": self.team_color})
            return aoo
        return None
