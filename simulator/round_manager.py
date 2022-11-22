from simulator.combat_manager import *
from simulator.teams import Teams
import logging

logger = logging.getLogger(__name__)


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
        logger.debug("--------------INITIATIVE ORDER--------------")
        for character in self.characters:
            logger.debug(f"{character.get_name()} with {character.get_curr_init()}")

    def is_only_one_team_standing(self):
        return True if len(self.__teams.get_surviving_teams()) == 1 else False

    def simulate_n(self, n=1):
        if n == 1:
            self.simulate()
        elif n > 1:
            team_tally = {name: 0 for name in self.__teams.get_team_names()}
            for i in range(n):
                self.simulate()
                surviving_teams = self.__teams.get_surviving_teams()
                if len(surviving_teams) > 1:
                    logger.warning("There's more than one surviving team. Battle's not over yet!")
                elif len(surviving_teams) == 0:
                    logger.warning("Everyone's dead. No winners!")
                else:
                    team_tally[surviving_teams[0]] += 1
                for ch in self.characters:
                    ch.reset()
            logger.info("--------------STATISTICS--------------")
            for name, victories in team_tally.items():
                logger.info(f"Team {name} won total of {victories} times", extra={"team": name})
        else:
            logger.error("Wrong input. n has to be 1 or higher!")

    def simulate(self):
        self.roll_initiative()
        self.order_by_initiative()
        logger.debug("--------------START--------------")
        for r in range(self.num_rounds):
            logger.debug(f"Round {r + 1}:")
            if self.is_only_one_team_standing():
                logger.debug("EARLY END")
                break
            for character in self.characters:
                if character.is_alive():
                    character.new_round()
                    while True:
                        action = character.get_action(self.battle_map)
                        if action is None:
                            break
                        if action.is_targeted_combat_action():
                            self.combat_manager.resolve_action(action)
                else:
                    logger.debug(f"Character {character.get_name()} is dead. Skipping")
            self.print_status()
        self.print_results()

    def print_status(self):
        for character in self.characters:
            status = f"alive with {character.get_curr_hp()}" if character.is_alive() else "dead"
            logger.debug(f"Character {character.get_name()} is {status}", extra={"team": self.__teams.get_team(character)})

    def print_results(self):
        logger.debug("--------------RESULT--------------")
        self.print_status()

