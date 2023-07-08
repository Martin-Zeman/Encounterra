import math
from simulator.actions.actoid import FactoryFlags
from simulator.actions.melee_attack import MeleeAttackFactory, MeleeAttack
from simulator.battle_map import Map
from simulator.misc import Size
import logging


logger = logging.getLogger("EncounTroll")

class BiteAndSwallowFactory(MeleeAttackFactory):

    def __init__(self, name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range=1, ammo=math.inf, on_hit=None, extra_dmg=[]):
        super().__init__(name, combatant, to_hit, dmg_dice, dmg_bonus, dmg_type, attack_range, action_type, crit_range, ammo, on_hit, extra_dmg)
        self.flags |= FactoryFlags.IS_MELEE

    def create(self, target):
        if self.combatant.constricted_target is target and target.is_alive() and target.size.value <= Size.MEDIUM.value:
            return BiteAndSwallow(target, self)
        return None

    def create_all(self):
        # if self.combatant.constricted_target is not None and self.combatant.constricted_target.size <= Size.MEDIUM:
        if self.combatant.constricted_target.is_alive():
            return [BiteAndSwallow(self.combatant.constricted_target, self)]
        return None



class BiteAndSwallow(MeleeAttack):

    def shorthand_str(self):
        return "Bite"

    def get_eligible_coords(self, distances, shortest_paths):
        try:
            battle_map = Map.get()
            return battle_map.get_free_coords_in_hop_range(battle_map.get_combatant_position(self.target),
                                                           distances,
                                                           inflate_to_size=self.factory.combatant.size,
                                                           rng=self.factory.range,
                                                           combatant=self.factory.combatant)
        except AttributeError:
            print("FIXME")

    def is_current_coord_eligible(self):
        battle_map = Map.get()
        return battle_map.are_in_hop_range(self.factory.combatant, self.target, self.factory.range)

    def calculate_threat(self, **kwargs):
        # The swallow itself it hard to quantify but we just need to make sure it wins out over the regular bite
        return self.factory.calculate_threat_to_target(self.target, **kwargs)

    def calculate_threat_delta(self, modifiers, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        battle_map = Map.get()
        return self.factory.calculate_threat_to_target_delta(battle_map, self.target, modifiers, *args, **kwargs)