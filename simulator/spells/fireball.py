from simulator.spells.spell import SpellStats
from simulator.misc import SavingThrow, DamageType, mean_dmg_dc_attack
from simulator.actoid import Actoid


class Fireball(Actoid):

    level = 3
    spell_range = SpellStats.Range.FEET_150
    target = SpellStats.Target.RADIUS_20
    duration = SpellStats.Duration.INSTANTANEOUS
    concentration = False
    type = SpellStats.Type.HARMFUL
    dmg_type = DamageType.Fire

    class Stats:
        def __init__(self, dc, eligible_action_types, **kwargs):
            self.dc
            self.eligible_action_types = eligible_action_types  # FIREBALL, QUICKENED_FIREBALL
            self.saving_throw = SavingThrow.DEX
            self.dmg_dice = "8d6"
            self.additional_upcast_dmg = "1d6"

        def find_best_args(self, combatant, battle_map):
            coord, _, _ = battle_map.find_best_placement_harmful_circular(combatant, self.spell_range.value, self.target.value)
            return coord


    def __init__(self, action_type, coord, stats, level=3, has_spell_sculpting=False, **kwargs):
        # self.empowered = False if "empowered" not in kwargs or not kwargs["empowered"] else True
        self.action_type = action_type
        self.coord = coord
        self.stats = stats
        self.empowered = False if "empowered" not in kwargs or not kwargs["empowered"] else True
        self.stats.level = min(max(level, 3), 9)


    @staticmethod
    def calculate_threat_approx(combatant, battle_map, *args, **kwargs):
        placement, _, affected = battle_map.find_best_placement_harmful_circular(combatant, SpellStats.Range.FEET_150.value, SpellStats.Target.RADIUS_20.value)
        acc = 0
        for aff in affected:
            acc += mean_dmg_dc_attack(combatant.dc, "8d6", True, aff.saving_throws[SavingThrow.DEX][0])
        return acc

    def calculate_threat(self, combatant, battle_map, *args, **kwargs):
        affected = battle_map.get_combatants_affected_by_aoe(combatant, self.stats.target, self.stats.type, self.coord)
        acc = 0
        for aff in affected:
            acc += mean_dmg_dc_attack(self.stats.dc, self.stats.dmg_dice, True, aff.saving_throws[self.stats.saving_throw][0])
        return acc
