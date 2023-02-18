from simulator.spells.spell import SpellStats
from simulator.misc import SavingThrow, DamageType, mean_dmg_dc_attack
from simulator.actions.actoid import Actoid, ActoidFlags
from simulator.threat_calculator import DirectThreat, DirectThreatFactory

class FireballFactory(DirectThreatFactory):
    def __init__(self, dc, action_type, caster, has_spell_sculpting=False, **kwargs):
        self.dc = dc
        self.action_type = action_type  # FIREBALL, QUICKENED_FIREBALL
        self.saving_throw = SavingThrow.DEX
        self.dmg_dice = "8d6"
        self.additional_upcast_dmg = "1d6"
        self.caster = caster
        self.has_spell_sculpting = has_spell_sculpting

    def find_best_args(self, combatant, battle_map):
        coord, _, _ = battle_map.find_best_placement_harmful_circular(combatant, Fireball.spell_range.value, SpellStats.TRANSLATE_RADIUS[Fireball.target])
        return coord

    def create_best(self, combatant, battle_map, **kwargs):
        return Fireball(self.find_best_args(combatant, battle_map), self,  **kwargs)

    def create(self, coord):
        return Fireball(coord, self)

    # def calculate_threat_approx(self, battle_map, *args, **kwargs):
    #     placement, _, affected = battle_map.find_best_placement_harmful_circular(self.caster, SpellStats.Range.FEET_150.value,
    #                                                                              SpellStats.Target.RADIUS_20.value)
    #     acc = 0
    #     for aff in affected:
    #         acc += mean_dmg_dc_attack(self.caster.dc, "8d6", True, aff.saving_throws[SavingThrow.DEX][0])
    #     return acc

    def calculate_threat_approx_mod(self, battle_map, modified_stats, *args, **kwargs):
        return 0 # no need

    def calculate_threat_to_target(self, battle_map, target, *args, **kwargs):
        """
        Calculates threat to one specific target
        """
        if battle_map.get_cartesian_distance(self.caster, target) <= Fireball.spell_range.value + SpellStats.TRANSLATE_RADIUS[Fireball.target]:
            return mean_dmg_dc_attack(self.dc, self.dmg_dice, True, target.saving_throws[self.saving_throw][0])
        else:
            return 0

    def calculate_threat_to_target_mod(self, battle_map, target, modified_stats, *args, **kwargs):
        """
        Calculates the threat delta of the factory to a specific target given stat modifications
        """
        return 0 # No need

class Fireball(Actoid, DirectThreat):

    level = 3
    spell_range = SpellStats.Range.FEET_150
    target = SpellStats.Target.RADIUS_20
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = False
    type = SpellStats.Type.HARMFUL
    dmg_type = DamageType.Fire


    def __init__(self, coord, factory,  **kwargs):
        super().__init__(actoid_type=ActoidFlags.IS_SPELL | ActoidFlags.IS_DIRECT_THREAT)
        # self.empowered = False if "empowered" not in kwargs or not kwargs["empowered"] else True
        self.coord = coord
        self.factory = factory
        self.empowered = False if "empowered" not in kwargs or not kwargs["empowered"] else True
        self.heightened = False if "heightened " not in kwargs or not kwargs["heightened "] else True

    def __str__(self):
        return "Fireball"


    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        affected = battle_map.get_combatants_affected_by_aoe(self.factory.caster, Fireball.target, Fireball.type, self.coord)
        acc = 0
        for aff in affected:
            acc += mean_dmg_dc_attack(self.factory.dc, self.factory.dmg_dice, True, aff.saving_throws[self.factory.saving_throw][0])
        return acc
