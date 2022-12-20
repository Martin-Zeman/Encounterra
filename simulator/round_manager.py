from simulator.combat_manager import *
from simulator.actoid import Actoid
from simulator.teams import Teams
import logging

logger = logging.getLogger(__name__)


class RoundManager:
    def __init__(self, combatants, teams, battle_map, combat_manager, num_rounds = 30):
        self.combatants = combatants
        self.teams = teams
        self.num_rounds = num_rounds
        self.battle_map = battle_map
        self.combat_manager = combat_manager

    def roll_initiative(self):
        for combatant in self.combatants:
            combatant.roll_initiative()

    def order_by_initiative(self):
        def by_initiative(e):
            return e.get_curr_init()

        self.combatants.sort(key=by_initiative, reverse=True)
        logger.debug("--------------INITIATIVE ORDER--------------")
        for combatant in self.combatants:
            logger.debug(f"{combatant.get_name()} with {combatant.get_curr_init()}")

    def goes_before_in_initiative(self, combatant1, combatant2):
        return True if self.combatants.index(combatant1) < self.combatants.index(combatant2) else False

    def is_only_one_team_standing(self):
        return True if len(self.teams.get_surviving_teams()) == 1 else False

    def request_movement(self, combatant, movement):
        if movement.incurs_aoo:
            aoo_candidates = self.battle_map.get_aoo_eligible_combatants(combatant, movement.increment)
            if aoo_candidates:
                for candidate in aoo_candidates:
                    aoo = candidate.prompt_aoo(combatant)
                    if aoo:
                        aoo.action_class = Action.ActionClasses.REACTION
                        self.combat_manager.resolve_attack(aoo)

            pam_candidates = self.battle_map.get_pam_eligible_combatants(combatant, movement.increment)
            if pam_candidates:
                for candidate in pam_candidates:
                    pam_attack = candidate.prompt_pam(combatant)
                    if pam_attack:
                        pam_attack.action_class = Action.ActionClasses.REACTION
                        if self.combat_manager.resolve_attack(pam_attack) and candidate.has_sentinel:
                            combatant.movement = 0
                            logger.debug(f"Combatant {combatant.get_name()} was stopped by sentinel")

        if combatant.is_alive():
            self.battle_map.move_combatant(combatant, movement.increment)
            return True
        return False


    def resolve_by_actoid_type(self, actoid, combatant):
        match actoid.actoid_type:
            case Actoid.Type.IS_TARGETED_COMBAT_ACTION:
                self.combat_manager.resolve_attack(actoid)
            case Actoid.Type.IS_MOVEMENT:
                if not self.request_movement(combatant, actoid):
                    return  # combatant didn't survive
            case Actoid.Type.IS_SPELL:
                self.combat_manager.resolve_spell(combatant, actoid)
            case Actoid.Type.IS_DODGE:
                combatant.is_dodging = True
            case _:
                logger.error("Unknown actoid type")

    def simulate_n(self, n=1):
        if n == 1:
            self.simulate()
        elif n > 1:
            team_tally = {name: 0 for name in self.teams.get_team_names()}
            combatant_initial_positions = {ch:self.battle_map.get_combatant_position(ch) for ch in self.combatants}
            for i in range(n):
                logger.info(f"{i}. Iteration")
                for combatant in self.combatants:
                    self.battle_map.set_combatant_coordinates(combatant, combatant_initial_positions[combatant])
                self.simulate()
                surviving_teams = self.teams.get_surviving_teams()
                if len(surviving_teams) > 1:
                    logger.warning("There's more than one surviving team. Battle's not over yet!")
                elif len(surviving_teams) == 0:
                    logger.warning("Everyone's dead. No winners!")
                else:
                    team_tally[surviving_teams[0]] += 1
                for ch in self.combatants:
                    ch.reset()
                self.battle_map.reset()
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
            for combatant in self.combatants:
                if combatant.is_alive():
                    combatant.new_turn()
                    while True:
                        action = combatant.get_action(self.battle_map)
                        if action is None:
                            break
                        self.resolve_by_actoid_type(action, combatant)
                else:
                    logger.debug(f"Combatant {combatant.get_name()} is dead. Skipping")
            self.print_status()
        # self.print_results()

    def print_status(self):
        for combatant in self.combatants:
            status = f"alive with {combatant.get_curr_hp()}" if combatant.is_alive() else "dead"
            logger.debug(f"Combatant {combatant.get_name()} is {status}", extra={"team": self.teams.get_team(combatant)})
        logger.debug(self.battle_map)

    def print_results(self):
        logger.debug("--------------RESULT--------------")
        self.print_status()

