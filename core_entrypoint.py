from simulator.logging.custom_logger import CustomLogger
from simulator.session import Session
from simulator.teams import Teams
from simulator.battle_map import Map

import boto3
import logging
import os


dynamodb = boto3.client('dynamodb', region_name='eu-west-1')  # TODO remove the region
s3 = boto3.client('s3')
bucket_name = "encounterra-simulation-results"
local_log_file_path = "/tmp/log.txt"
CustomLogger(logging.INFO, False, local_log_file_path)
logger = logging.getLogger("Encounterra")

def handler(event, context):
    logger.info("------CORE LAMBDA STARTING------")
    if os.path.exists(local_log_file_path):
        os.remove(local_log_file_path)
    Map.reset_singleton()
    logger.info(f"event {event}")
    input = event['core_input']
    blue_team = input['blue']
    red_team = input['red']
    job_id = input['job_id']
    index = event['index']

    subdirectory = f"{job_id}/{index}/"

    session = Session()
    for blue_combatant in blue_team:
        session.add_combatant(blue_combatant, Teams.Color.BLUE)
    for red_combatant in red_team:
        session.add_combatant(red_combatant, Teams.Color.RED)
    session.set_num_simulations(1)
    try:
        result = session.simulate(parallel=False)

        blue_victory = int(result[Teams.Color.BLUE])
        red_victory = int(not blue_victory)
        s3_object_key = subdirectory + f'{"blue" if result[Teams.Color.BLUE] else "red"}_victory_log.txt'
        s3.upload_file(local_log_file_path, bucket_name, s3_object_key)
        logger.info(f"{job_id}:{index} SUCCESS")
        return {
            'blue_victory': blue_victory,
            'red_victory': red_victory
        }
    except Exception as e:
        logger.error(f"{job_id}:{index} FAILURE: {e}")
        exit(1)
