from .combatants.assassin_rogue_5lvl import AssassinRogue5Lvl
from .combatants.brown_bear import BrownBear
from .combatants.bugbear import Bugbear
from .combatants.dire_wolf import DireWolf
from .combatants.dragonclaw_cultist import DragonclawCultist
from .combatants.evil_mage import EvilMage
from .combatants.giant_toad import GiantToad
from .combatants.goblin import Goblin
from .combatants.moon_druid_5lvl import MoonDruid5Lvl
from .combatants.ogre import Ogre
from .combatants.stone_giant import StoneGiant
from .combatants.totem_barbarian_5lvl import TotemBarbarian5Lvl
from .combatants.draconic_sorcerer_5lvl import DraconicSorcerer5Lvl
from .effects.effect_tracker import EffectTracker
from .utils.utils import get_combatant_classes
from .battle_map import *
from .round_manager import *
from .teams import Teams
from enum import Enum
import logging
import multiprocessing as mp


logger = logging.getLogger("Encounterra")


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
        self.character_type_counter = {cls: 1 for cls in get_combatant_classes()}
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
            case "DraconicSorcerer5Lvl":
                self.combatants.append(DraconicSorcerer5Lvl("DraconicSorcerer5Lvl " + str(curr_count)))
            case "TotemBarbarian5Lvl":
                self.combatants.append(TotemBarbarian5Lvl("TotemBarbarian5Lvl" + str(curr_count)))
            case "DragonclawCultist":
                self.combatants.append(DragonclawCultist("DragonclawCultist " + str(curr_count)))
            case "Goblin":
                self.combatants.append(Goblin("Goblin " + str(curr_count)))
            case "Bugbear":
                self.combatants.append(Bugbear("Bugbear " + str(curr_count)))
            case "Ogre":
                self.combatants.append(Ogre("Ogre " + str(curr_count)))
            case "StoneGiant":
                self.combatants.append(StoneGiant("StoneGiant " + str(curr_count)))
            case "MoonDruid5Lvl":
                self.combatants.append(MoonDruid5Lvl("MoonDruid5Lvl " + str(curr_count)))
            case "AssassinRogue5Lvl":
                self.combatants.append(AssassinRogue5Lvl("AssassinRogue5Lvl " + str(curr_count)))
            case "DragonclawCultist":
                self.combatants.append(DragonclawCultist("DragonclawCultist " + str(curr_count)))
            case "GiantToad":
                self.combatants.append(GiantToad("GiantToad " + str(curr_count)))
            case "BrownBear":
                self.combatants.append(BrownBear("BrownBear " + str(curr_count)))
            case "DireWolf":
                self.combatants.append(DireWolf("DireWolf " + str(curr_count)))
            case "EvilMage":
                self.combatants.append(EvilMage("EvilMage " + str(curr_count)))
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
            random_coords = Coords(random_coord, combatant.size)
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
        self.round_manager = RoundManager(self.combatants, self.teams, self.effect_tracker)
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
            return accumulated_tally
        else:
            return self.round_manager.simulate_n(self.num_simulations)