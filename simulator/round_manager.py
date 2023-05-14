from simulator.action_resolver import *
from simulator.resources import reset_resources
from simulator.effects.effect_tracker import EffectTracker
import logging
import copy

logger = logging.getLogger("EncounTroll")


class RoundManager:
    def __init__(self, combatants, teams, battle_map, effect_tracker, num_rounds=30):
        self.combatants = combatants
        self.teams = teams
        self.num_rounds = num_rounds
        self.battle_map = battle_map
        self.effect_tracker = effect_tracker
        self.action_resolver = ActionResolver(combatants, teams, battle_map, self.effect_tracker)

    def roll_initiative(self):
        for combatant in self.combatants:
            combatant.roll_initiative()

    def order_by_initiative(self):
        def by_initiative(e):
            return e.curr_init

        self.combatants.sort(key=by_initiative, reverse=True)
        logger.info("--------------INITIATIVE ORDER--------------")
        for combatant in self.combatants:
            logger.info(f"{combatant} with {combatant.curr_init}", extra={"team": combatant.team_color})

    def goes_before_in_initiative(self, combatant1, combatant2):
        return True if self.combatants.index(combatant1) < self.combatants.index(combatant2) else False

    def is_only_one_team_standing(self):
        return True if len(self.teams.get_surviving_teams()) == 1 else False

    def reset(self, combatant_initial_positions):
        for combatant in self.combatants:
            reset_resources(combatant)
        self.effect_tracker.reset()
        self.battle_map.reset(combatant_initial_positions)


    def simulate_n(self, n=1, result_queue=None):
        if n > 0:
            team_tally = {color: 0 for color in self.teams.get_team_colors()}
            combatant_initial_positions = {c: copy.deepcopy(self.battle_map.get_combatant_position(c).get()[0]) for c in self.combatants}
            for i in range(n):
                logger.warning(f"{i}. Iteration")
                self.simulate()
                surviving_teams = self.teams.get_surviving_teams()
                if len(surviving_teams) > 1:
                    logger.warning("There's more than one surviving team. Battle's not over yet!")
                elif len(surviving_teams) == 0:
                    logger.warning("Everyone's dead. No winners!")
                else:
                    logger.warning(f"Team {surviving_teams[0].name} wins")
                    team_tally[surviving_teams[0]] += 1
                self.reset(combatant_initial_positions)
            if result_queue:
                result_queue.put(team_tally)
            logger.warning("--------------STATISTICS--------------")
            for name, victories in team_tally.items():
                logger.warning(f"Team {name.name} won total of {victories} times", extra={"team": name})
        else:
            logger.error("Wrong input. n has to be 1 or higher!")

    def simulate(self):
        self.roll_initiative()
        self.order_by_initiative()
        done = False
        logger.info("--------------START--------------")
        for r in range(self.num_rounds):
            logger.info(f"Round {r + 1}:")
            if done:
                logger.info("The fight is over")
                break
            for combatant in self.combatants:
                if done:
                    break
                if not combatant.is_alive():
                    continue
                logger.info(f"It's {combatant}'s turn")
                logger.info(self.battle_map)
                self.effect_tracker.new_turn(combatant)
                combatant.new_turn()
                effects = self.effect_tracker.get_all_affecting_combatant(combatant)
                self.action_resolver.resolve_effects(effects, combatant)
                if combatant.is_affected_by_any(Conditions.STUNNED, Conditions.PARALYZED, Conditions.PETRIFIED,
                                                Conditions.UNCONSCIOUS):
                    logger.info(f"{combatant} is affected by a condition which prevents any action. Skipping turn")
                    self.effect_tracker.new_turn(combatant)
                    continue
                while True:
                    # try:
                    action = combatant.get_action(self.battle_map)
                    # except TypeError as e:
                        # logger.error(f"{combatant} threw {e} for action {action}")
                    if action is None:
                        break
                    self.action_resolver.resolve_action(action, combatant)
                    if self.is_only_one_team_standing():
                        done = True
                        break
                    if not combatant.is_alive():
                        break  # could have died as a result of AoO
                if combatant.is_alive():
                    self.effect_tracker.new_turn(combatant)
                else:
                    self.effect_tracker.combatant_died(combatant)
            self.print_status()

    def print_status(self):
        for combatant in self.combatants:
            status = f"alive with {combatant.curr_hp}" if combatant.is_alive() else "dead"
            logger.info(f"Combatant {combatant} is {status}", extra={"team": self.teams.get_team(combatant)})
        logger.info(self.battle_map)

    def print_results(self):
        logger.info("--------------RESULT--------------")
        self.print_status()
