from .combatants.acolyte import Acolyte
from .combatants.assassin import Assassin
from .combatants.assassin_rogue_3lvl import AssassinRogue3Lvl
from .combatants.assassin_rogue_5lvl import AssassinRogue5Lvl
from .combatants.bandit import Bandit
from .combatants.bandit_captain import BanditCaptain
from .combatants.berserker import Berserker
from .combatants.brown_bear import BrownBear
from .combatants.bugbear import Bugbear
from .combatants.bugbear_chief import BugbearChief
from .combatants.commoner import Commoner
from .combatants.cultist import Cultist
from .combatants.cultist_fanatic import CultistFanatic
from .combatants.dire_wolf import DireWolf
from .combatants.draconic_sorcerer_3lvl import DraconicSorcerer3Lvl
from .combatants.draconic_sorcerer_5lvl import DraconicSorcerer5Lvl
from .combatants.dragonclaw_cultist import DragonclawCultist
from .combatants.evil_mage import EvilMage
from .combatants.giant_constrictor_snake import GiantConstrictorSnake
from .combatants.giant_spider import GiantSpider
from .combatants.giant_toad import GiantToad
from .combatants.goblin import Goblin
from .combatants.moon_druid_3lvl import MoonDruid3Lvl
from .combatants.moon_druid_5lvl import MoonDruid5Lvl
from .combatants.needle_blight import NeedleBlight
from .combatants.night_hag import NightHag
from .combatants.ogre import Ogre
from .combatants.quetzalcoatlus import Quetzalcoatlus
from .combatants.saber_toothed_tiger import SaberToothedTiger
from .combatants.stone_giant import StoneGiant
from .combatants.totem_barbarian_5lvl import TotemBarbarian5Lvl
from .combatants.twig_blight import TwigBlight
from .combatants.vampire_spawn import VampireSpawn
from .effects.effect_tracker import EffectTracker
from .resources import ResourceDepletionLevel
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
        TWO_SIDES = 1
        RANDOM = 2
        SURROUNDED = 3

    class MapType(Enum):
        BLANK = "blank"
        OBSTACLES = "obstacles"
        DIFFICULT_TERRAIN = "difficult_terrain"
        OBSTACLES_AND_DIFFICULT_TERRAIN = "obstacles_and_difficult_terrain"
        DOUBLE_OBSTACLES = "double_obstacles"
        DOUBLE_DIFFICULT_TERRAIN = "double_difficult_terrain"
        HALLWAY = "hallway"

    def __init__(self):
        self.combatants = []
        self.num_simulations = 1
        self.map_size = 15
        self.statistic_collector = None
        self.character_type_counter = {cls.id: 1 for cls in get_combatant_classes()}
        self.teams = Teams()
        self.battle_map = Map(self.map_size, self.teams)
        self.placement_scenario = self.PlacementScenario.TWO_SIDES
        self.round_manager = None
        self.effect_tracker = EffectTracker()
        self.battle_map.set_effect_tracker(self.effect_tracker)

    def serialize_data(self):
        data = {
            'combatants': self.combatants,
            'teams': self.teams,
            'effect_tracker': self.effect_tracker,
            'round_manager': self.round_manager,
            # Add other attributes as needed
        }
        return data

    def deserialize_data(self, data):
        self.combatants = data['combatants']
        self.teams = data['teams']
        self.effect_tracker = data['effect_tracker']
        self.round_manager = data['round_manager']

    def add_combatant(self, combatant_type, team, resource_depletion_level=ResourceDepletionLevel.FULLY_RESTED):
        if type(combatant_type) is not int:
            combatant_type = combatant_type.id  # we want to allow both kinds of calls
        try:
            curr_count = self.character_type_counter[combatant_type]
        except KeyError:
            logger.error(f"Unknown combatant type: {combatant_type}")
            return

        # TODO use character_type_counter instead
        match combatant_type:
            case Acolyte.id:
                self.combatants.append(Acolyte(curr_count))
            case Assassin.id:
                self.combatants.append(Assassin(curr_count))
            case AssassinRogue3Lvl.id:
                self.combatants.append(AssassinRogue3Lvl(curr_count))
            case AssassinRogue5Lvl.id:
                self.combatants.append(AssassinRogue5Lvl(curr_count))
            case Bandit.id:
                self.combatants.append(Bandit(curr_count))
            case BanditCaptain.id:
                self.combatants.append(BanditCaptain(curr_count))
            case Berserker.id:
                self.combatants.append(Berserker(curr_count))
            case BrownBear.id:
                self.combatants.append(BrownBear(curr_count))
            case Bugbear.id:
                self.combatants.append(Bugbear(curr_count))
            case BugbearChief.id:
                self.combatants.append(BugbearChief(curr_count))
            case Commoner.id:
                self.combatants.append(Commoner(curr_count))
            case Cultist.id:
                self.combatants.append(Cultist(curr_count))
            case CultistFanatic.id:
                self.combatants.append(CultistFanatic(curr_count))
            case DireWolf.id:
                self.combatants.append(DireWolf(curr_count))
            case DraconicSorcerer3Lvl.id:
                self.combatants.append(DraconicSorcerer3Lvl(curr_count))
            case DraconicSorcerer5Lvl.id:
                self.combatants.append(DraconicSorcerer5Lvl(curr_count))
            case DragonclawCultist.id:
                self.combatants.append(DragonclawCultist(curr_count))
            case EvilMage.id:
                self.combatants.append(EvilMage(curr_count))
            case GiantConstrictorSnake.id:
                self.combatants.append(GiantConstrictorSnake(curr_count))
            case GiantSpider.id:
                self.combatants.append(GiantSpider(curr_count))
            case GiantToad.id:
                self.combatants.append(GiantToad(curr_count))
            case Goblin.id:
                self.combatants.append(Goblin(curr_count))
            case MoonDruid3Lvl.id:
                self.combatants.append(MoonDruid3Lvl(curr_count))
            case MoonDruid5Lvl.id:
                self.combatants.append(MoonDruid5Lvl(curr_count))
            case NeedleBlight.id:
                self.combatants.append(NeedleBlight(curr_count))
            case NightHag.id:
                self.combatants.append(NightHag(curr_count))
            case Ogre.id:
                self.combatants.append(Ogre(curr_count))
            case Quetzalcoatlus.id:
                self.combatants.append(Quetzalcoatlus(curr_count))
            case SaberToothedTiger.id:
                self.combatants.append(SaberToothedTiger(curr_count))
            case StoneGiant.id:
                self.combatants.append(StoneGiant(curr_count))
            case TotemBarbarian5Lvl.id:
                self.combatants.append(TotemBarbarian5Lvl(curr_count))
            case TwigBlight.id:
                self.combatants.append(TwigBlight(curr_count))
            case VampireSpawn.id:
                self.combatants.append(VampireSpawn(curr_count))
            case _:
                logger.error(f"Unknown combatant type: {combatant_type}")
                return
        self.character_type_counter[combatant_type] += 1
        self.combatants[-1].deplete_resources(resource_depletion_level)
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
            if self.battle_map.are_empty(random_coords):
                logger.warning(f"Setting initial position {random_coords.get()[0]} for {combatant}")
                self.battle_map.set_combatant_coordinates(combatant, random_coord)
                break

    def place_combatants_on_the_map(self):
        match self.placement_scenario:
            case self.PlacementScenario.TWO_SIDES:
                logger.info("Combatant placement: Two Sides")
                for combatant in self.combatants:
                    team_color = self.teams.get_team_color_code(combatant)
                    right_bounds = [0, self.map_size // 2 - 1] if team_color is Teams.Color.BLUE else [self.map_size // 2 + 1, self.map_size - 1]
                    self.place_combatant(combatant, [0, self.map_size - 1], right_bounds)
            case self.PlacementScenario.RANDOM:
                logger.info("Combatant placement: Fully Random")
                for combatant in self.combatants:
                    self.place_combatant(combatant, [0, self.map_size - 1], [0, self.map_size - 1])
            case _:
                logger.error("Unsupported placement scenario. Going with default")
                self.placement_scenario = self.PlacementScenario.TWO_SIDES
                self.place_combatants_on_the_map()

    def place_terrain_and_obstacles(self, map_type):
        match map_type:
            case Session.MapType.BLANK.value:
                logger.info("Map Type: Blank")
            case Session.MapType.OBSTACLES.value:
                logger.info("Map Type: Obstacles")
                self.battle_map.place_circular_element((random.randint(0, self.map_size - 1), random.randint(0, self.map_size - 1)), Terrain.IMPASSABLE_TERRAIN, random.randint(0, 1))
                self.battle_map.place_circular_element((random.randint(0, self.map_size - 1), random.randint(0, self.map_size - 1)), Terrain.IMPASSABLE_TERRAIN, random.randint(0, 1))
            case Session.MapType.DOUBLE_OBSTACLES.value:
                logger.info("Map Type: Double Obstacles")
                self.battle_map.place_circular_element((random.randint(0, self.map_size - 1), random.randint(0, self.map_size - 1)), Terrain.IMPASSABLE_TERRAIN, random.randint(0, 1))
                self.battle_map.place_circular_element((random.randint(0, self.map_size - 1), random.randint(0, self.map_size - 1)), Terrain.IMPASSABLE_TERRAIN, random.randint(0, 1))
                self.battle_map.place_circular_element((random.randint(0, self.map_size - 1), random.randint(0, self.map_size - 1)), Terrain.IMPASSABLE_TERRAIN, random.randint(0, 1))
                self.battle_map.place_circular_element((random.randint(0, self.map_size - 1), random.randint(0, self.map_size - 1)), Terrain.IMPASSABLE_TERRAIN, random.randint(0, 1))
            case Session.MapType.OBSTACLES_AND_DIFFICULT_TERRAIN.value:
                logger.info("Map Type: Obstacles & Difficult Terrain")
                self.battle_map.place_circular_element((random.randint(0, self.map_size - 1), random.randint(0, self.map_size - 1)), Terrain.DIFFICULT_TERRAIN, random.randint(0, 1))
                self.battle_map.place_circular_element((random.randint(0, self.map_size - 1), random.randint(0, self.map_size - 1)), Terrain.DIFFICULT_TERRAIN, random.randint(0, 1))
                self.battle_map.place_circular_element((random.randint(0, self.map_size - 1), random.randint(0, self.map_size - 1)), Terrain.IMPASSABLE_TERRAIN,random.randint(0, 1))
                self.battle_map.place_circular_element((random.randint(0, self.map_size - 1), random.randint(0, self.map_size - 1)), Terrain.IMPASSABLE_TERRAIN, random.randint(0, 1))
            case Session.MapType.DIFFICULT_TERRAIN.value:
                logger.info("Map Type: Difficult Terrain")
                self.battle_map.place_circular_element((random.randint(0, self.map_size - 1), random.randint(0, self.map_size - 1)), Terrain.DIFFICULT_TERRAIN, random.randint(0, 1))
                self.battle_map.place_circular_element((random.randint(0, self.map_size - 1), random.randint(0, self.map_size - 1)), Terrain.DIFFICULT_TERRAIN, random.randint(0, 1))
            case Session.MapType.DOUBLE_DIFFICULT_TERRAIN.value:
                logger.info("Map Type: Double Difficult Terrain")
                self.battle_map.place_circular_element((random.randint(0, self.map_size - 1), random.randint(0, self.map_size - 1)), Terrain.DIFFICULT_TERRAIN, random.randint(0, 1))
                self.battle_map.place_circular_element((random.randint(0, self.map_size - 1), random.randint(0, self.map_size - 1)), Terrain.DIFFICULT_TERRAIN, random.randint(0, 1))
                self.battle_map.place_circular_element((random.randint(0, self.map_size - 1), random.randint(0, self.map_size - 1)), Terrain.DIFFICULT_TERRAIN, random.randint(0, 1))
                self.battle_map.place_circular_element((random.randint(0, self.map_size - 1), random.randint(0, self.map_size - 1)), Terrain.DIFFICULT_TERRAIN, random.randint(0, 1))
            case Session.MapType.HALLWAY.value:
                logger.info("Map Type: Hallway")
                for idx in range(15):
                    self.battle_map.place_circular_element((0, idx), Terrain.IMPASSABLE_TERRAIN, 0)
                    self.battle_map.place_circular_element((1, idx), Terrain.IMPASSABLE_TERRAIN, 0)
                    self.battle_map.place_circular_element((2, idx), Terrain.IMPASSABLE_TERRAIN, 0)
                    self.battle_map.place_circular_element((3, idx), Terrain.IMPASSABLE_TERRAIN, 0)
                    self.battle_map.place_circular_element((11, idx), Terrain.IMPASSABLE_TERRAIN, 0)
                    self.battle_map.place_circular_element((12, idx), Terrain.IMPASSABLE_TERRAIN, 0)
                    self.battle_map.place_circular_element((13, idx), Terrain.IMPASSABLE_TERRAIN, 0)
                    self.battle_map.place_circular_element((14, idx), Terrain.IMPASSABLE_TERRAIN, 0)
            case _:
                logger.info("Map Type: Blank by Default")

    def simulate(self, parallel=False):
        self.round_manager = RoundManager(self.combatants, self.teams, self.effect_tracker)  # TODO remove the effect_tracker
        self.place_combatants_on_the_map()
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
