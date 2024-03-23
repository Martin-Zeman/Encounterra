import logging
import math
from functools import cache

from cachetools import cached
from cachetools.keys import hashkey

from ..actions.action_types import BonusAction
from ..battle_map import Map
from ..effects.action_enabler_effect import ActionEnablerEffect
from ..effects.limited_duration_effect import LimitedDurationEffect
from ..conditions import Conditions, is_affected_by_any
from ..spells.spell import SpellStats
from ..effects.effect import EffectType
from ..actions.actoid import Actoid, ActoidFlags
from ..threat_interfaces import DirectThreat
from ..factory_interfaces import ThreatModifierFactory

logger = logging.getLogger("Encounterra")


class ShillelaghFactory(ThreatModifierFactory):
    level = 0
    range = SpellStats.Range.TOUCH
    target = SpellStats.Target.SELF
    duration = SpellStats.Duration.MINUTE
    concentration = False
    type = SpellStats.Type.BUFF
    dc = None
    dmg_type = None

    def __init__(self, caster, resource, original_attack, new_attack):
        super().__init__()
        self.action_type = BonusAction.SHILLELAGH
        self.combatant = caster
        self.resource = resource
        self.original_attack = original_attack
        self.new_attack = new_attack

    def __str__(self):
        """
        Important for FSM building
        """
        return "ShillelaghFactory"

    def get_ability_name(self):
        return "Shillelagh"

    def create_all(self, previous_action_in_dag=None):
        if self.combatant.ammo[self.new_attack.name] != math.inf:
            return [Shillelagh(self)]
        return []

    def calculate_threat_to_target(self, target, **kwargs):
        return 0

    def calculate_max_threat(self):
        # if self.new_attack.ammo != math.inf:
        #     return self.new_attack.calculate_max_threat() - self.original_attack.calculate_max_threat()
        return 0


class Shillelagh(Actoid, LimitedDurationEffect, ActionEnablerEffect, DirectThreat):
    def __init__(self, factory):
        Actoid.__init__(self, ActoidFlags.IS_SPELL)
        LimitedDurationEffect.__init__(self, factory.combatant, turns=10)
        self.factory = factory

    def __str__(self):
        return f"Shillelagh on {self.factory.new_attack}"

    def shorthand_str(self):
        return "Shillelagh"

    def get_effect_type(self):
        return EffectType.SHILLELAGH

    def activate(self, **kwargs):
        logger.info(f"{self.factory.combatant} casts Shillelagh on {self.factory.original_attack.name}")
        self.factory.combatant.ammo[self.factory.new_attack.name] = math.inf

    def deactivate(self):
        logger.info(f"Shillelagh on {self.factory.original_attack.name} fades")
        self.factory.combatant.ammo[self.factory.new_attack.name] = 0

    def deactivate_for_combatant(self, combatant):
        assert False

    def is_affecting(self, combatant):
        return False

    def enable(self):
        self.factory.combatant.ammo[self.factory.new_attack.name] = math.inf

    def disable(self):
        self.factory.combatant.ammo[self.factory.new_attack.name] = 0

    def calculate_threat(self, **kwargs):
        return 0
        # return self.factory.calculate_max_threat()

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        return 0


    #@map_toggled_cache_with_key(key=lambda self, distances, shortest_paths: hashkey(self.factory.name, tuple(Map.get().get_combatant_position(self.factory.combatant).get()[0])))
    def get_eligible_coords(self, distances, shortest_paths):
        battle_map = Map.get()
        if not is_affected_by_any(self.factory.combatant, Conditions.GRAPPLED, Conditions.GRAPPLING,
                                  Conditions.RESTRAINED):
            return battle_map.get_all_accessible_coords(shortest_paths, self.factory.combatant)
        return [tuple(battle_map.get_combatant_position(self.factory.combatant).get()[0])]
