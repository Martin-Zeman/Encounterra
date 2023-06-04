from simulator.combatants.bugbear import Bugbear
from simulator.combatants.dragonclaw_cultist import DragonclawCultist
from simulator.combatants.goblin import Goblin
from simulator.combatants.moon_druid_5lvl import MoonDruid5Lvl
from simulator.combatants.ogre import Ogre
from simulator.combatants.stone_giant import StoneGiant
from simulator.combatants.totem_barbarian_5lvl import TotemBarbarian5Lvl
from simulator.combatants.faurung import Faurung
from simulator.combatants.cyanwrath import Cyanwrath
from simulator.battle_map import *
from simulator.round_manager import *
from simulator.teams import Teams
# from RL.faurung_env import FaurungEnv
from enum import Enum
import logging
import multiprocessing as mp

logger = logging.getLogger("EncounTroll")


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
            TotemBarbarian5Lvl: 1,
            DragonclawCultist: 1,
            Cyanwrath: 1,
            Goblin: 1,
            Bugbear: 1,
            Ogre: 1,
            StoneGiant: 1,
            MoonDruid5Lvl: 1
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
                self.combatants.append(Faurung(self.effect_tracker, "Faurung " + str(curr_count)))
            case "TotemBarbarian5Lvl":
                self.combatants.append(TotemBarbarian5Lvl(self.effect_tracker, "TotemBarbarian5Lvl" + str(curr_count)))
            case "Cyanwrath":
                self.combatants.append(Cyanwrath(self.effect_tracker))
            case "DragonclawCultist":
                self.combatants.append(DragonclawCultist(self.effect_tracker, "DragonclawCultist " + str(curr_count)))
            case "Goblin":
                self.combatants.append(Goblin(self.effect_tracker, "Goblin " + str(curr_count)))
            case "Bugbear":
                self.combatants.append(Bugbear(self.effect_tracker, "Bugbear " + str(curr_count)))
            case "Ogre":
                self.combatants.append(Ogre(self.effect_tracker, "Ogre " + str(curr_count)))
            case "StoneGiant":
                self.combatants.append(StoneGiant(self.effect_tracker, "StoneGiant " + str(curr_count)))
            case "MoonDruid5Lvl":
                self.combatants.append(MoonDruid5Lvl(self.effect_tracker, "MoonDruid5Lvl " + str(curr_count)))
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
        # Make sure larger combatants fit
        offset = 0
        if combatant.size.value > Size.MEDIUM.value:
            offset = combatant.size.value
        bounds1[1] -= offset
        bounds2[1] -= offset
        while True:
            # TODO place some kind of a timeout here
            random_coord = np.array([random.randint(*bounds1), random.randint(*bounds2)])
            random_coords = CombatantCoords(random_coord, combatant)
            logger.warning(f"Setting initial position {random_coords.get()[0]} for {combatant}")
            if self.battle_map.are_empty(random_coords):
                self.battle_map.set_combatant_coordinates(combatant, random_coord)
                break

    def place_combatants_on_the_map(self):
        match self.placement_scenario:
            case self.PlacementScenario.TWO_HALVES:
                for combatant in self.combatants:
                    team_color = self.teams.get_team_color_code(combatant)
                    right_bounds = [0, self.map_size // 2 - 1] if team_color is Teams.Color.BLUE else [self.map_size // 2 + 1, self.map_size - 1]
                    self.place_combatant(combatant, [0, self.map_size - 1], right_bounds)
            case self.PlacementScenario.TOTALLY_RANDOM:
                for combatant in self.combatants:
                    self.place_combatant(combatant, [0, self.map_size - 1], [0, self.map_size - 1])
            case _:
                logger.error("Unsupported placement scenario. Going with default")
                self.placement_scenario = self.PlacementScenario.TWO_HALVES
                self.place_combatants_on_the_map()

    def place_random_elements_on_the_map(self):
        self.battle_map.place_circular_element((random.randint(0, self.map_size - 1), random.randint(0, self.map_size - 1)), Terrain.DIFFICULT_TERRAIN, random.randint(0, 1))
        self.battle_map.place_circular_element((random.randint(0, self.map_size - 1), random.randint(0, self.map_size - 1)), Terrain.DIFFICULT_TERRAIN, random.randint(0, 1))
        self.battle_map.place_circular_element((random.randint(0, self.map_size - 1), random.randint(0, self.map_size - 1)), Terrain.IMPASSABLE_TERRAIN, random.randint(0, 1))
        self.battle_map.place_circular_element((random.randint(0, self.map_size - 1), random.randint(0, self.map_size - 1)), Terrain.IMPASSABLE_TERRAIN, random.randint(0, 1))

    def simulate(self, parallel=False):
        self.battle_map = Map(self.map_size, self.teams)
        self.battle_map.set_effect_tracker(self.effect_tracker)
        self.effect_tracker.set_battle_map(self.battle_map)
        self.round_manager = RoundManager(self.combatants, self.teams, self.battle_map, self.effect_tracker)
        self.place_random_elements_on_the_map()
        self.place_combatants_on_the_map()
        for combatant in self.combatants:
            combatant.set_round_manager(self.round_manager)
        self.battle_map.build_adjacency_matrix()
        if parallel and self.num_simulations >= mp.cpu_count():
            # mp.set_start_method('spawn')
            result_acc = mp.Queue()
            # jobs = [mp.Process(target=self.round_manager.simulate_n, args=(self.num_simulations // mp.cpu_count(), result_acc)) for _ in range(self.num_simulations // mp.cpu_count())]
            jobs = []
            for _ in range(mp.cpu_count()):
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
            logger.warning("--------------STATISTICS--------------")
            for name, victories in accumulated_tally.items():
                logger.warning(f"Team {name.name} won total of {victories} times", extra={"team": name})
        else:
            self.round_manager.simulate_n(self.num_simulations)