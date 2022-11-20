from simulator.map import *
from simulator.round_manager import *
from simulator.teams import Teams
from simulator.characters.rena import Rena
from simulator.characters.cyanwrath import Cyanwrath
import logging
import sys
from simulator.logging.log_formatter import LogFormatter
from simulator.logging.color_adapter import ColorAdapter


class CustomLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        yellow = '\x1b[38;5;226m'
        reset = '\x1b[0m'
        return yellow + f'{msg}' + reset, kwargs

if __name__ == '__main__':
    # redbrand_shortsword = attack(4, '1d6', 2)
    # print_ac_dc_range(12, 18, [redbrand_shortsword, redbrand_shortsword], "Redbrand")
    #
    # manticore_bite = attack(5, '1d8', 3)
    # manticore_claw = attack(5, '1d6', 3)
    # manticore_tail_spike = attack(5, '1d8', 3)
    # print_ac_dc_range(12, 18, [manticore_bite, manticore_claw, manticore_claw], "Manticore melee")
    # print_ac_dc_range(12, 18, [manticore_tail_spike, manticore_tail_spike, manticore_tail_spike], "Manticore ranged")
    #
    # test_dc_attack = dc_attack(10, '1d10', False)
    # print_ac_dc_range(0, 3, [test_dc_attack], "Test")
    #
    # acid_spray = dc_attack(13, '3d6', True)
    # print_ac_dc_range(0, 7, [acid_spray], "Ankheg")

    # owlbear_attacks = [Attack(7, "1d10", 5), Attack(7, "2d8", 5)]
    # owlbear = Combatant("Owlbear", owlbear_attacks, 59, 13, 1)
    # rena_attacks = [Attack(5, "1d12", 3)]
    # rena = Combatant("Rena", rena_attacks, 70, 14, 10)
    # simulate_n_combats(owlbear, rena, 100000)

    # grick_attacks = [Attack(4, "2d6", 2), Attack(4, "1d6", 2)]
    # grick = Combatant("Grick", grick_attacks, 52, 14, 2)
    # simulate_n_combats(grick, rena, 1000)

    # cyanwrath_attacks = [Attack(7, "1d10", 4, [19,20]), Attack(7, "1d10", 4, [19,20]),  Attack(7, "1d4", 4, [19,20])]
    # rena_attacks = [Attack(7, "1d12", 4), Attack(7, "1d12", 4)]
    # Cyanwrath = Combatant("Cyanwrath", cyanwrath_attacks, 95, 17, 1)
    # Rena = Combatant("Rena", rena_attacks, 122, 15, 1)
    # simulate_n_combats(Cyanwrath, Rena, 10000)

    #--------------------------------------------------
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    stdout_handler.setFormatter(LogFormatter())
    logger.addHandler(stdout_handler)

    cyanwrath = Cyanwrath()
    rena = Rena()
    combatants = [cyanwrath, rena]
    teams = Teams()
    teams.add_char_to_team(cyanwrath, "Blue")
    teams.add_char_to_team(rena, "Red")
    battle_map = Map(10, 10, teams)
    battle_map.set_character_coordinates(cyanwrath, 4, 5)
    battle_map.set_character_coordinates(rena, 5, 5)
    combat_manager = CombatManager(combatants, teams)
    round_manager = RoundManager(combatants, teams, battle_map, combat_manager)
    round_manager.simulate_n(1000)
    # round_manager.print_results()

