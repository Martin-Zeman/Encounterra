from ..abilities.on_hit_effect import OnHit
from ..misc import Class, avg_roll, _roll_dice, DamageType
import logging

logger = logging.getLogger("Encounterra")


class OnHitDivineSmite(OnHit):

    @staticmethod
    def get_dmg_dice(spell_slot_level):
        match spell_slot_level:
            case 1:
                return (2, 8)
            case 2:
                return (3, 8)
            case 3:
                return (4, 8)
            case 4:
                return (5, 8)
            case _:
                logger.error("Incorrect Divine Smite Level")
                return (2, 8)

    @staticmethod
    def get_dmg_dice_undead_or_fiend(spell_slot_level):
        match spell_slot_level:
            case 1:
                return (3, 8)
            case 2:
                return (4, 8)
            case 3:
                return (5, 8)
            case 4:
                return (6, 8)
            case _:
                logger.error("Incorrect Divine Smite Level")
                return (3, 8)

    def __init__(self, name="Divine Smite"):
        self.name = name

    def hit(self, attacker, attack, target, multiplier, dmg_so_far):
        for level in range(4, 0, -1):
            if attacker.spellslots.has_resource(level=level):
                target_hp = target.curr_hp
                dmg_dice = OnHitDivineSmite.get_dmg_dice_undead_or_fiend(level) if (type(target).cls is Class.MONSTER.UNDEAD or type(target).cls is Class.MONSTER.FIEND) else OnHitDivineSmite.get_dmg_dice(level)
                avg_dmg = avg_roll(dmg_dice)
                if (target_hp - dmg_so_far) * 1.3 >= avg_dmg * multiplier:
                    attacker.spellslots.use_resource(level=level)
                    logger.error(f"{attacker} uses Divine Smite of level {level} on {target}")
                    return [_roll_dice(dmg_dice) * multiplier, DamageType.Radiant]
        return None

    def calculate_threat(self, attacker, target, **kwargs):
        dmg_acc = 0
        count = 0
        for level in range(4, 0, -1):
            if attacker.spellslots.has_resource(level=level):
                dmg_dice = OnHitDivineSmite.get_dmg_dice_undead_or_fiend(level) if (type(target).cls is Class.MONSTER.UNDEAD or type(target).cls is Class.MONSTER.FIEND) else OnHitDivineSmite.get_dmg_dice(level)
                dmg_acc = avg_roll(dmg_dice)
                count += 1
        if count:
            dmg_acc /= count
        return dmg_acc
