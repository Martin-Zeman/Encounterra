from simulator.combatants.dragonclaw_cultist import DragonclawCultist
from simulator.combatants.totem_barbarian_5lvl import TotemBarbarian5Lvl
from simulator.combatants.faurung import Faurung
from simulator.combatants.faurung_dt import FaurungDt
from simulator.combatants.cyanwrath import Cyanwrath
from simulator.map import *
from simulator.round_manager import *
from simulator.teams import Teams
from RL.faurung_env import FaurungEnv
from enum import Enum
import logging
import multiprocessing as mp

logger = logging.getLogger(__name__)


class Session:

    class PlacementScenario(Enum):
        TWO_HALVES = 1
        SURROUNDED = 2
        TOTALLY_RANDOM = 3

    def __init__(self):
        self.combatants = []
        self.num_simulations = 1
        self.battle_map = None
        self.map_size = 15
        self.statistic_collector = None
        self.character_type_counter = {
            Faurung: 1,
            FaurungDt: 1,
            TotemBarbarian5Lvl: 1,
            DragonclawCultist: 1,
            Cyanwrath: 1
        }
        self.teams = Teams()
        self.placement_scenario = self.PlacementScenario.TWO_HALVES
        self.round_manager = None
        self.effect_tracker = EffectTracker()

    def add_combatant(self, combatant_type, team):
        try:
            curr_count = self.character_type_counter[combatant_type]
        except KeyError:
            logger.error("Unknown combatant type")
            return

        match combatant_type.__name__:
            case "Faurung":
                self.combatants.append(Faurung(self.effect_tracker))
            case "FaurungDt":
                self.combatants.append(FaurungDt(self.effect_tracker))
            case "TotemBarbarian5Lvl":
                self.combatants.append(TotemBarbarian5Lvl(self.effect_tracker))
            case "Cyanwrath":
                self.combatants.append(Cyanwrath(self.effect_tracker))
            case "DragonclawCultist":
                self.combatants.append(DragonclawCultist(self.effect_tracker, "DragonclawCultist " + str(curr_count)))
            case _:
                logger.error("Unknown combatant type")
                return
        self.character_type_counter[combatant_type] += 1
        self.teams.add_combatant_to_team(self.combatants[-1], team)


    def set_map_type(self):
        pass

    def set_map_size(self, size):
        self.map_size = size

    def set_num_simulations(self, num):
        assert num > 0
        self.num_simulations = num

    def set_placement_scenario(self, scenario):
        assert isinstance(scenario, self.PlacementScenario)
        self.placement_scenario = scenario

    def place_combatant(self, combatant, bounds1, bounds2):
        while True:
            # TODO place some kind of a timeout here
            random_coord = np.array([random.randint(*bounds1), random.randint(*bounds2)])
            if self.battle_map.is_empty(random_coord):
                self.battle_map.set_combatant_coordinates(combatant, random_coord)
                break

    def place_combatants_on_the_map(self):
        match self.placement_scenario:
            case self.PlacementScenario.TWO_HALVES:
                for combatant in self.combatants:
                    team_color = self.teams.get_team_color_code(combatant)
                    right_bounds = (0, self.map_size // 2 - 1) if team_color is Teams.Color.BLUE else (self.map_size // 2 + 1, self.map_size - 1)
                    self.place_combatant(combatant, (0, self.map_size - 1), right_bounds)
            case self.PlacementScenario.TOTALLY_RANDOM:
                for combatant in self.combatants:
                    self.place_combatant(combatant, (0, self.map_size - 1), (0, self.map_size - 1))
            case _:
                logger.error("Unsupported placement scenario. Going with default")
                self.placement_scenario = self.PlacementScenario.TWO_HALVES
                self.place_combatants_on_the_map()

    def place_random_elements_on_the_map(self):
        self.battle_map.place_circular_element((random.randint(0, self.map_size - 1), random.randint(0, self.map_size - 1)), Terrain.DIFFICULT_TERRAIN, random.randint(1, 2))
        self.battle_map.place_circular_element((random.randint(0, self.map_size - 1), random.randint(0, self.map_size - 1)), Terrain.DIFFICULT_TERRAIN, random.randint(1, 2))
        self.battle_map.place_circular_element((random.randint(0, self.map_size - 1), random.randint(0, self.map_size - 1)), Terrain.IMPASSABLE_TERRAIN, random.randint(1, 2))
        self.battle_map.place_circular_element((random.randint(0, self.map_size - 1), random.randint(0, self.map_size - 1)), Terrain.IMPASSABLE_TERRAIN, random.randint(1, 2))

    def simulate(self, parallel=False):
        self.battle_map = Map(self.map_size, self.teams)
        self.battle_map.set_effect_tracker(self.effect_tracker)
        self.round_manager = RoundManager(self.combatants, self.teams, self.battle_map, self.effect_tracker)
        self.place_combatants_on_the_map()
        for combatant in self.combatants:
            combatant.set_round_manager(self.round_manager)
        self.place_random_elements_on_the_map()
        self.battle_map.build_adjacency_matrix()
        if parallel:
            result_acc = mp.Queue()
            # jobs = [mp.Process(target=self.round_manager.simulate_n, args=(self.num_simulations // mp.cpu_count(), result_acc)) for _ in range(self.num_simulations // mp.cpu_count())]
            jobs = []
            for _ in range(mp.cpu_count() - 1 if self.num_simulations % mp.cpu_count() else mp.cpu_count()):
                jobs.append(mp.Process(target=self.round_manager.simulate_n, args=(self.num_simulations // mp.cpu_count(), result_acc)))
            if self.num_simulations % mp.cpu_count():
                jobs.append(mp.Process(target=self.round_manager.simulate_n, args=(self.num_simulations % mp.cpu_count(), result_acc)))
            for job in jobs:
                job.start()
            for job in jobs:
                job.join()
            accumulated_tally = {}
            while not result_acc.empty():
                tally = result_acc.get()
                for key, val in tally.items():
                    try:
                        accumulated_tally[key] += val
                    except KeyError:
                        accumulated_tally[key] = val
            logger.info("--------------STATISTICS--------------")
            for name, victories in accumulated_tally.items():
                logger.info(f"Team {name.name} won total of {victories} times", extra={"team": name})
        else:
            self.round_manager.simulate_n(self.num_simulations)