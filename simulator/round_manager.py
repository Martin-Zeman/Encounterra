from .action_resolver import *
from .actions.action_selector import get_action
from .misc import Statistics
from .resources import reset_resources
from .teams import Teams
from .utils.utils import preallocate_wildshape_forms
import logging
import copy

logger = logging.getLogger("Encounterra")


class RoundManager:
    def __init__(self, combatants, teams, effect_tracker, num_rounds=30):
        self.combatants = combatants
        self.teams = teams
        self.num_rounds = num_rounds
        self.effect_tracker = effect_tracker
        self.action_resolver = ActionResolver(combatants, teams, self.effect_tracker)

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

    def prep_combatants(self):
        """
        Secondary initialization. It's an optimization measure.
        """
        for combatant in self.combatants:
            for baf in combatant.bonus_action_factories:
                if baf[0] is BonusAction.MOON_WILDSHAPE:
                    combatant.available_wildshape_forms = preallocate_wildshape_forms(combatant, BonusAction.MOON_WILDSHAPE, baf[1])
                    break
            for af in combatant.action_factories:
                if af[0] is Action.WILDSHAPE:
                    combatant.available_wildshape_forms = preallocate_wildshape_forms(combatant, Action.WILDSHAPE, af[1])
                    break


    def goes_before_in_initiative(self, combatant1, combatant2):
        return True if self.combatants.index(combatant1) < self.combatants.index(combatant2) else False

    def is_only_one_team_standing(self):
        return True if len(self.teams.get_surviving_teams()) == 1 else False

    def reset(self, combatant_initial_positions):
        for combatant in self.combatants:
            reset_resources(combatant)
        self.effect_tracker.reset()
        Map.get().reset(combatant_initial_positions)


    def simulate_n(self, n=1, result_queue=None):
        if n > 0:
            team_tally = {color: {stat: 0 for stat in Statistics} for color in self.teams.get_team_colors()}
            combatant_initial_positions = {c: copy.deepcopy(Map.get().get_combatant_position(c).get()[0]) for c in self.combatants}
            self.prep_combatants()
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
                    team_tally[surviving_teams[0]][Statistics.VICTORIES] += 1
                    dead_blue, dead_red = self.teams.get_death_count()
                    if dead_blue > 0:
                        team_tally[Teams.Color.BLUE][Statistics.AT_LEAST_ONE_DIED] += 1
                    if dead_red > 0:
                        team_tally[Teams.Color.RED][Statistics.AT_LEAST_ONE_DIED] += 1
                    if dead_blue > 1:
                        team_tally[Teams.Color.BLUE][Statistics.AT_LEAST_TWO_DIED] += 1
                    if dead_red > 1:
                        team_tally[Teams.Color.RED][Statistics.AT_LEAST_TWO_DIED] += 1
                    if dead_blue > 2:
                        team_tally[Teams.Color.BLUE][Statistics.AT_LEAST_THREE_DIED] += 1
                    if dead_red > 2:
                        team_tally[Teams.Color.RED][Statistics.AT_LEAST_THREE_DIED] += 1

                self.reset(combatant_initial_positions)
            if result_queue:
                result_queue.put(team_tally)
            # logger.warning("--------------STATISTICS--------------")
            # for name, victories in team_tally.items():
            #     logger.warning(f"Team {name.name} won total of {victories} times", extra={"team": name})
            return team_tally
        else:
            logger.error("Wrong input. n has to be 1 or higher!")
        return None

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
                logger.info(Map.get())
                self.effect_tracker.start_of_turn(combatant)
                if not combatant.is_alive():  # Start of turn effects can kill
                    continue
                combatant.new_turn()
                effects = self.effect_tracker.get_affecting_combatant(combatant)  # TODO consider cleaning this up by merging with start_of_turn
                self.action_resolver.resolve_effects(effects, combatant)
                if combatant.is_affected_by_any(Conditions.INCAPACITATED, Conditions.STUNNED, Conditions.PARALYZED, Conditions.PETRIFIED, Conditions.UNCONSCIOUS):
                    logger.info(f"{combatant} is affected by a condition which prevents any action. Skipping turn")
                    # self.effect_tracker.start_of_turn(combatant)
                    self.effect_tracker.end_of_turn(combatant)
                    combatant.on_end_of_turn()
                    continue
                while True:
                    action = get_action(combatant)
                    if action is None:
                        break
                    resolution = self.action_resolver.resolve_action(action, combatant)
                    if resolution is None:
                        break
                    if self.is_only_one_team_standing():
                        done = True
                        break
                    if not combatant.is_alive():
                        self.effect_tracker.combatant_died(combatant)
                        break  # could have died as a result of AoO
                if combatant.is_alive():
                    self.effect_tracker.end_of_turn(combatant)
                    combatant.on_end_of_turn()
            logger.info("----------------------------------")
            self.print_status()

    def print_status(self):
        for combatant in self.combatants:
            combatant = combatant.get_current_form()
            status = f"alive with {combatant.curr_hp} hp" if combatant.is_alive() else "dead"
            logger.info(f"{combatant} is {status}", extra={"team": self.teams.get_team(combatant)})
        logger.info(Map.get())

    def print_results(self):
        logger.info("--------------RESULT--------------")
        self.print_status()
