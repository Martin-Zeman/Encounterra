from simulator.action_resolver import *
from simulator.feasibility import check_feasibility
from simulator.resources import use_resource, reset_resources
from simulator.action_factory import action_factory
from simulator.action_factory import Passive
from simulator.effects.effect_tracker import EffectTracker
import logging

logger = logging.getLogger(__name__)


class RoundManager:
    def __init__(self, combatants, teams, battle_map, num_rounds=30):
        self.combatants = combatants
        self.teams = teams
        self.num_rounds = num_rounds
        self.battle_map = battle_map
        self.effect_tracker = EffectTracker()
        self.action_resolver = ActionResolver(combatants, teams, battle_map, self.effect_tracker)


    def roll_initiative(self):
        for combatant in self.combatants:
            combatant.roll_initiative()

    def order_by_initiative(self):
        def by_initiative(e):
            return e.curr_init

        self.combatants.sort(key=by_initiative, reverse=True)
        logger.debug("--------------INITIATIVE ORDER--------------")
        for combatant in self.combatants:
            logger.debug(f"{combatant} with {combatant.curr_init}")

    def goes_before_in_initiative(self, combatant1, combatant2):
        return True if self.combatants.index(combatant1) < self.combatants.index(combatant2) else False

    def is_only_one_team_standing(self):
        return True if len(self.teams.get_surviving_teams()) == 1 else False


    def reset(self, combatant_initial_positions):
        for combatant in self.combatants:
            reset_resources(combatant)
        self.battle_map.reset()
        for combatant in self.combatants:
            # TODO consider making this part of map reset
            self.battle_map.set_combatant_coordinates(combatant, combatant_initial_positions[combatant])

    def simulate_n(self, n=1, result_queue=None):
        if n > 0:
            team_tally = {color: 0 for color in self.teams.get_team_colors()}
            combatant_initial_positions = {ch: self.battle_map.get_combatant_position(ch) for ch in self.combatants}
            for i in range(n):
                logger.info(f"{i}. Iteration")
                self.simulate()
                surviving_teams = self.teams.get_surviving_teams()
                if len(surviving_teams) > 1:
                    logger.warning("There's more than one surviving team. Battle's not over yet!")
                elif len(surviving_teams) == 0:
                    logger.warning("Everyone's dead. No winners!")
                else:
                    team_tally[surviving_teams[0]] += 1
                self.reset(combatant_initial_positions)
            if result_queue:
                result_queue.put(team_tally)
            logger.info("--------------STATISTICS--------------")
            for name, victories in team_tally.items():
                logger.info(f"Team {name.name} won total of {victories} times", extra={"team": name})
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
            for combatant in self.combatants:
                if combatant.is_alive():
                    combatant.new_turn()
                    self.effect_tracker.new_turn(combatant)
                    while True:
                        try:
                            action, *args = combatant.get_action(self.battle_map)
                        except TypeError as e:
                            logger.error(f"FIXME {combatant} threw {e} for action {action} with {args}")
                        if action is None:
                            break
                        self.action_resolver.resolve_action(action, args, combatant)
                        if not combatant.is_alive():
                            break  # could have died as a result of AoO
                else:
                    logger.debug(f"Combatant {combatant} is dead. Skipping")
            self.print_status()

    def print_status(self):
        for combatant in self.combatants:
            status = f"alive with {combatant.curr_hp}" if combatant.is_alive() else "dead"
            logger.debug(f"Combatant {combatant} is {status}", extra={"team": self.teams.get_team(combatant)})
        logger.debug(self.battle_map)

    def print_results(self):
        logger.debug("--------------RESULT--------------")
        self.print_status()
