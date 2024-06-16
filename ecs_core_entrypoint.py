import pickle
import time
import traceback
import re
import json
from datetime import datetime

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


def simplify_movements(log_lines):
    simplified_logs = []
    previous_entity = None
    previous_line = None

    # Adjusted pattern to match the movement lines, including the optional space
    move_pattern = re.compile(r"^(.*?moved to \[\s?\d+\s+\d+\])$")

    for line in log_lines:
        move_match = move_pattern.match(line)

        if move_match:
            # Extract the entity part before " moved to"
            current_entity = move_match.group(1).split(" moved to")[0]

            if current_entity == previous_entity:
                previous_line = line  # Update the previous line to the current one
            else:
                if previous_line:
                    simplified_logs.append(previous_line)  # Append the previous movement line
                previous_entity = current_entity
                previous_line = line
        else:
            if previous_line:
                simplified_logs.append(previous_line)  # Append the last movement line
                previous_entity = None
                previous_line = None
            simplified_logs.append(line)

    if previous_line:
        simplified_logs.append(previous_line)  # Append the last movement line if any

    return simplified_logs


def upload_simulation_results_to_s3(job_id, index, result):
    simulation_results = {
        'blue_victory': result[Teams.Color.BLUE][Statistics.VICTORIES],
        'red_victory': result[Teams.Color.RED][Statistics.VICTORIES],
        'blue_at_least_one_died': result[Teams.Color.BLUE][Statistics.AT_LEAST_ONE_DIED],
        'red_at_least_one_died': result[Teams.Color.RED][Statistics.AT_LEAST_ONE_DIED],
        'blue_at_least_two_died': result[Teams.Color.BLUE][Statistics.AT_LEAST_TWO_DIED],
        'red_at_least_two_died': result[Teams.Color.RED][Statistics.AT_LEAST_TWO_DIED],
        'blue_at_least_three_died': result[Teams.Color.BLUE][Statistics.AT_LEAST_THREE_DIED],
        'red_at_least_three_died': result[Teams.Color.RED][Statistics.AT_LEAST_THREE_DIED],
    }

    json_data = json.dumps(simulation_results, indent=4)

    json_file_key = f"{job_id}/{index}/simulation_results.json"

    s3.put_object(
        Bucket=results_bucket_name,
        Key=json_file_key,
        Body=json_data.encode('utf-8'),
        ContentType='application/json'
    )


if os.path.exists(local_log_file_path):
    os.remove(local_log_file_path)
CustomLogger(logging.INFO, False, local_log_file_path)
logger = logging.getLogger("Encounterra")
Map.reset_singleton()

# Fetching input data from environment variables
blue_team = os.getenv('BLUE_TEAM', '').split(',')  # Assuming blue team IDs are comma-separated in env var
red_team = os.getenv('RED_TEAM', '').split(',')    # Assuming red team IDs are comma-separated in env var
combatant_placement = int(os.getenv('COMBATANT_PLACEMENT', '0'))  # Assuming combatant placement as integer
blue_depletion_level = int(os.getenv('BLUE_DEPLETION_LEVEL', '0'))  # Assuming depletion level as integer
red_depletion_level = int(os.getenv('RED_DEPLETION_LEVEL', '0'))    # Assuming depletion level as integer
map_type = os.getenv('MAP_TYPE', '')
job_id = os.getenv('JOB_ID', '')
index = os.getenv('INDEX', '')

date_suffix = datetime.now().strftime("%Y%m%d-%H%M")
job_id_with_suffix = f"{job_id}_{date_suffix}"
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

    with open(local_log_file_path, 'r') as file:
        log_lines = file.readlines()
    simplified_logs = simplify_movements(log_lines)
    with open(local_log_file_path, 'w') as file:
        file.writelines(simplified_logs)

    blue_victory = result[Teams.Color.BLUE][Statistics.VICTORIES]

    s3_object_key = subdirectory + f'{"blue" if blue_victory == 1 else "red"}_victory_log.txt'
    s3.upload_file(local_log_file_path, results_bucket_name, s3_object_key)

    # Temporarily upload simulation results to S3 for aggregation
    upload_simulation_results_to_s3(job_id, index, result)
except Exception as e:
    error_message = traceback.format_exc()
    logger.error(f"{job_id}:{index} FAILURE: {error_message}")
    try:
        timestamp = int(time.time())
        logger.info(f"Serializing error with timestamp: {timestamp}")
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
        s3.upload_file(battle_map_data_path, crash_bucket_name, f"{job_id_with_suffix}/" + battle_map_data)
        s3.upload_file(session_data_path, crash_bucket_name, f"{job_id_with_suffix}/" + session_data)
        s3.upload_file(exception_data_path, crash_bucket_name, f"{job_id_with_suffix}/" + exception_data)
        s3.upload_file(local_log_file_path, crash_bucket_name, f"{job_id_with_suffix}/log_{timestamp}.txt")
    except Exception as serialization_e:
        logger.error(f"Failed to serialize and upload objects: {serialization_e}")
    exit(1)
