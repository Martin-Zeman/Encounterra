import pickle
import time

from simulator.logging.custom_logger import CustomLogger
from simulator.misc import Statistics
from simulator.resources import ResourceDepletionLevel
from simulator.session import Session
from simulator.teams import Teams
from simulator.battle_map import Map

import boto3
import logging
import os


dynamodb = boto3.client('dynamodb', region_name='eu-west-1')  # TODO remove the region
s3 = boto3.client('s3')
results_bucket_name = "encounterra-simulation-results"
crash_bucket_name = "encounterra-simulation-crashes"
local_log_file_path = "/tmp/log.txt"


def handler(event, context):
    if os.path.exists(local_log_file_path):
        os.remove(local_log_file_path)
    CustomLogger(logging.INFO, False, local_log_file_path)
    logger = logging.getLogger("Encounterra")
    Map.reset_singleton()
    core_input = event['core_input']
    blue_team = core_input['blue']
    red_team = core_input['red']
    combatant_placement = int(event['combatant_placement'])
    blue_depletion_level = int(event['blue_depletion_level'])
    red_depletion_level = int(event['red_depletion_level'])
    map_type = event['map_type']
    job_id = event['job_id']
    index = event['index']

    subdirectory = f"{job_id}/{index}/"

    session = Session()
    session.set_placement_scenario(Session.PlacementScenario(combatant_placement))
    session.place_terrain_and_obstacles(map_type)
    match blue_depletion_level:
        case ResourceDepletionLevel.FULLY_RESTED.value:
            logger.info("Blue Team is fully rested")
        case ResourceDepletionLevel.PARTIALLY_DEPLETED.value:
            logger.info("Blue Team is partially depleted")
        case ResourceDepletionLevel.FULLY_DEPLETED.value:
            logger.info("Blue Team is fully depleted")
        case _:
            logger.error("Unknown resource depletion level for the Blue Team")
    match red_depletion_level:
        case ResourceDepletionLevel.FULLY_RESTED.value:
            logger.info("Red Team is fully rested")
        case ResourceDepletionLevel.PARTIALLY_DEPLETED.value:
            logger.info("Red Team is partially depleted")
        case ResourceDepletionLevel.FULLY_DEPLETED.value:
            logger.info("Red Team is fully depleted")
        case _:
            logger.error("Unknown resource depletion level for the Red Team")
    for blue_combatant in blue_team:
        session.add_combatant(int(blue_combatant), Teams.Color.BLUE, ResourceDepletionLevel(blue_depletion_level))
    for red_combatant in red_team:
        session.add_combatant(int(red_combatant), Teams.Color.RED, ResourceDepletionLevel(red_depletion_level))
    session.set_num_simulations(1)
    try:
        result = session.simulate(parallel=False)

        blue_victory = result[Teams.Color.BLUE][Statistics.VICTORIES]

        s3_object_key = subdirectory + f'{"blue" if blue_victory == 1 else "red"}_victory_log.txt'
        s3.upload_file(local_log_file_path, results_bucket_name, s3_object_key)
        # logger.info(f"{job_id}:{index} SUCCESS")
        return {
            'blue_victory': result[Teams.Color.BLUE][Statistics.VICTORIES],
            'red_victory': result[Teams.Color.RED][Statistics.VICTORIES],
            'blue_at_least_one_died': result[Teams.Color.BLUE][Statistics.AT_LEAST_ONE_DIED],
            'red_at_least_one_died': result[Teams.Color.RED][Statistics.AT_LEAST_ONE_DIED],
            'blue_at_least_two_died': result[Teams.Color.BLUE][Statistics.AT_LEAST_TWO_DIED],
            'red_at_least_two_died': result[Teams.Color.RED][Statistics.AT_LEAST_TWO_DIED],
            'blue_at_least_three_died': result[Teams.Color.BLUE][Statistics.AT_LEAST_THREE_DIED],
            'red_at_least_three_died': result[Teams.Color.RED][Statistics.AT_LEAST_THREE_DIED],
        }
    except Exception as e:
        logger.error(f"{job_id}:{index} FAILURE: {e}")
        try:
            timestamp = int(time.time())
            battle_map_data = f'battle_map_data_{timestamp}.pkl'
            battle_map_data_path = '/tmp/' + battle_map_data
            session_data = f'session_{timestamp}.pkl'
            session_data_path = '/tmp/' + session_data
            exception_data = f'exception_{timestamp}.txt'
            exception_data_path = '/tmp/' + exception_data
            with open(battle_map_data_path, 'wb') as f:
                pickle.dump(Map.serialize_data(), f)
            with open(session_data_path, 'wb') as f:
                pickle.dump(session.serialize_data(), f)
            with open(exception_data_path, 'w') as f:
                f.write(f"Fuzzy test with Blue team {blue_team} and Red team {red_team} raised an exception:\n{e}")
            s3.upload_file(battle_map_data_path, crash_bucket_name, battle_map_data)
            s3.upload_file(session_data_path, crash_bucket_name, session_data)
            s3.upload_file(exception_data_path, crash_bucket_name, exception_data)
        except Exception as serialization_e:
            logger.error(f"Failed to serialize and upload objects: {serialization_e}")
        exit(1)
