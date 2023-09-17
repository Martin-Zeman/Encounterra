import json

from simulator.logging.custom_logger import CustomLogger
from simulator.session import Session
from simulator.teams import Teams

# import os
import boto3
# import argparse
import logging


dynamodb = boto3.client('dynamodb', region_name='eu-west-1')  # TODO remove the region
s3 = boto3.client('s3')
bucket_name = "encounterra-simulation-results"
local_log_file_path = "/tmp/log.txt"
local_stats_file_path = "/tmp/statistics.txt"
CustomLogger(logging.INFO, True, local_log_file_path)
logger = logging.getLogger("Encounterra")

def handler(event, context):

    logger.info("------CORE LAMBDA STARTING------")
    logger.info(f"event {event}")
    blue_team = event['blue']
    red_team = event['red']
    job_id = event['job_id']
    index = event.get('index')

    # parser = argparse.ArgumentParser()
    #
    # parser.add_argument('-b', '--blue', nargs='+', type=str, help='The blue team combatants')
    # parser.add_argument('-r', '--red', nargs='+', type=str, help='the red team combatants')
    # args = parser.parse_args()
    # blue_team = args.blue
    # red_team = args.red

    # batch_job_id = os.environ.get("AWS_BATCH_JOB_ID", None)
    # batch_array_idx = os.environ.get("AWS_BATCH_JOB_ARRAY_INDEX", None)
    # if not (batch_job_id and batch_array_idx):
    #     logger.error(f"Failed to get either batch_job_id or batch_array_idx.")
    #     exit(1)
    # batch_job_id = batch_job_id.split(":")[0]
    subdirectory = f"{job_id}/{index}/"
    # logger.info(f"batch_job_id: {batch_job_id}")
    # logger.info(f"batch_array_idx: {batch_array_idx}")

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
        # with open(local_stats_file_path, 'w') as stats_file:
        #     stats_file.write(f"BLUE {blue_victory}\nRED {red_victory}\n")
        #
        s3_object_key = subdirectory + f'{"blue" if result[Teams.Color.BLUE] else "red"}_victory_log.txt'
        s3.upload_file(local_log_file_path, bucket_name, s3_object_key)
        # s3.upload_file(local_stats_file_path, bucket_name, f"{batch_job_id}/{batch_array_idx}/statistics.txt")
        logger.info(f"{job_id}:{index} SUCCESS")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'core_results': {
                    'blue_victory': blue_victory,
                    'red_victory': red_victory
                }
            })
        }
    except Exception as e:
        # logger.error(f"{batch_job_id}:{batch_array_idx} FAILURE: {e}")
        logger.error(f"{job_id} FAILURE: {e}")
        exit(1)
