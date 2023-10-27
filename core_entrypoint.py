from simulator.logging.custom_logger import CustomLogger
from simulator.misc import Statistics
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

def handler(event, context):
    if os.path.exists(local_log_file_path):
        os.remove(local_log_file_path)
    CustomLogger(logging.INFO, False, local_log_file_path)
    logger = logging.getLogger("Encounterra")
    # logger.info("------CORE LAMBDA STARTING------")
    Map.reset_singleton()
    core_input = event['core_input']
    blue_team = core_input['blue']
    red_team = core_input['red']
    job_id = event['job_id']
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

        blue_victory = result[Teams.Color.BLUE][Statistics.VICTORIES]

        s3_object_key = subdirectory + f'{"blue" if blue_victory == 1 else "red"}_victory_log.txt'
        s3.upload_file(local_log_file_path, bucket_name, s3_object_key)
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
        exit(1)
