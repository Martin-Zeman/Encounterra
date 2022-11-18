from simulator.combat_manager import *
from simulator.team import Teams
import logging

class RoundManager:
    def __init__(self, characters, teams, battle_map, combat_manager, num_rounds = 20):
        self.characters = characters
        self.__teams = teams
        self.num_rounds = num_rounds
        self.battle_map = battle_map
        self.combat_manager = combat_manager

    def roll_initiative(self):
        for character in self.characters:
            character.roll_initiative()

    def order_by_initiative(self):
        def by_initiative(e):
            return e.get_curr_init()

        self.characters.sort(key=by_initiative, reverse=True)
        logging.debug("--------------INITIATIVE ORDER--------------")
        for character in self.characters:
            logging.debug(f"{character.get_name()} with {character.get_curr_init()}")

    def is_only_one_team_standing(self):
        return True if len(self.__teams.get_surviving_teams()) == 1 else False
        # team_head_count = {}
        # for character in self.characters:
        #     if character.is_alive():
        #         try:
        #             team_head_count[character.get_team()] += 1
        #         except KeyError:
        #             team_head_count[character.get_team()] = 1
        # num_teams_standing = 0
        # for key, val in team_head_count.items():
        #     if val:
        #         num_teams_standing += 1
        #         if num_teams_standing > 1:
        #             return False
        # return True

    def simulate_n(self, n=1):
        if n == 1:
            self.simulate()
        elif n > 1:
            logging.basicConfig(level=logging.INFO)
            team_tally = {name: 0 for name in self.__teams.get_team_names()}
            for i in range(n):
                self.simulate()
                surviving_teams = self.__teams.get_surviving_teams()
                if len(surviving_teams) > 1:
                    logging.warning("There's more than one surviving team. Battle's not over yet!")
                elif len(surviving_teams) == 0:
                    logging.warning("Everyone's dead. No winners!")
                else:
                    team_tally[surviving_teams[0]] += 1
                for ch in self.characters:
                    ch.reset()
            logging.info("--------------STATISTICS--------------")
            for name, victories in team_tally.items():
                logging.info(f"Team {name} won total of {victories} times")
        else:
            logging.error("Wrong input. n has to be 1 or higher!")

    def simulate(self):
        self.roll_initiative()
        self.order_by_initiative()
        logging.debug("--------------START--------------")
        for r in range(self.num_rounds):
            logging.debug(f"Round {r + 1}:")
            if self.is_only_one_team_standing():
                logging.debug("EARLY END")
                break
            for character in self.characters:
                if character.is_alive():
                    character.new_round()
                    while True:
                        action = character.get_action(self.battle_map)
                        if action is None:
                            break
                        self.combat_manager.resolve_action(action)
                    # if (self.is_only_one_team_standing()):
                    #     print("EARLY END")
                    #     return
                else:
                    logging.debug(f"Character {character.get_name()} is dead. Skipping")
            self.print_status()
        self.print_results()

    def print_status(self):
        for character in self.characters:
            status = f"alive with {character.get_curr_hp()}" if character.is_alive() else "dead"
            logging.debug(f"Character {character.get_name()} is {status}")

    def print_results(self):
        logging.debug("--------------RESULT--------------")
        self.print_status()

