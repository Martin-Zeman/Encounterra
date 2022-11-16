import re
from scipy.stats import randint
from functools import partial, reduce

def parse_dmg_dice(dice_string):
    p = re.compile('(\d+)d(\d+)')
    m = p.match(dice_string)
    num_dice = int(m.group(1))
    dice_size = int(m.group(2))
    return num_dice, dice_size

def mean_dmg(attack_bonus, dmg_dice, dmg_bonus, ac):
    rv = randint(1, 21, attack_bonus)
    p_hit = 1.0 - rv.cdf(ac)
    num_dice, dice_size = parse_dmg_dice(dmg_dice)
    avg_dmg_die_roll = num_dice * ((1.0 + dice_size)/2.0)
    return (avg_dmg_die_roll + dmg_bonus) * p_hit + 0.05 * avg_dmg_die_roll

def print_ac_dc_range(min, max, attacks, monster_name="Monster"):
    print(monster_name + ":")
    for i in range(min, max + 1):
        dmg_sum = reduce((lambda a, b: a + b), [a(i) for a in attacks])
        print("{:d}: {:.2f}".format(i, dmg_sum))
    print()

def attack(to_hit, hit_dice, dmg_bonus):
    return partial(mean_dmg, to_hit, hit_dice, dmg_bonus)

def mean_dmg_dc_attack(dc, dmg_dice, half_on_success, st_bonus):
    num_dice, dice_size = parse_dmg_dice(dmg_dice)
    avg_dmg_die_roll = num_dice * ((1.0 + dice_size)/2.0)
    rv = randint(1, 21, st_bonus)
    p_fail = rv.cdf(dc)
    fail_dmg = avg_dmg_die_roll * p_fail
    final_avg_dmg = fail_dmg + avg_dmg_die_roll/2.0 * (1.0 - p_fail) if half_on_success else fail_dmg
    return final_avg_dmg

def dc_attack(dc, dmg_dice, half_on_success):
    return partial(mean_dmg_dc_attack, dc, dmg_dice, half_on_success)