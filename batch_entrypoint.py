from simulator.combatants.bugbear import Bugbear
from simulator.logging.custom_logger import CustomLogger
from simulator.session import Session
from simulator.combatants.dragonclaw_cultist import DragonclawCultist
from simulator.teams import Teams

import os
import boto3
# import argparse
import logging
from botocore.exceptions import ClientError


# def write_to_dynamodb(batch_job_id: str, batch_array_idx: str, finished: bool, failed: bool, blue_victories=0, red_victories=0):
#     try:
#         response = dynamodb.put_item(
#             TableName=table_name,
#             Item={
#                 'batch_job_id': {'S': batch_job_id},
#                 'batch_array_idx': {'S': batch_array_idx},
#                 'finished': {'BOOL': finished},
#                 'failed': {'BOOL': failed},
#                 'blue_victories': {'N': str(blue_victories)},
#                 'red_victories': {'N': str(red_victories)},
#             }
#         )
#         return response
#     except ClientError as e:
#         print(e)
#         return None


dynamodb = boto3.client('dynamodb')
s3 = boto3.client('s3')
# table_name = 'simulation_tracking'
bucket_name = "encounterra-simulation-results"
# Define the local file you want to upload
local_file_path = "/tmp/log.txt"
CustomLogger(logging.INFO, True, local_file_path)
logger = logging.getLogger("Encounterra")
logger.info("------CORE BATCH JOB STARTING------")

# parser = argparse.ArgumentParser()

# parser.add_argument('--list-arg', nargs='+', type=str, help='A list of strings')
# args = parser.parse_args()

batch_job_id = value = os.environ.get("AWS_BATCH_JOB_ID", None)
batch_array_idx = os.environ.get("AWS_BATCH_JOB_ARRAY_INDEX", None)
if not (batch_job_id and batch_array_idx):
    logger.error(f"Failed to get either batch_job_id or batch_array_idx.")
    exit(1)
batch_job_id = batch_job_id.split(":")[0]
subdirectory = f"{batch_job_id}/{batch_array_idx}/"
logger.info(f"batch_job_id: {batch_job_id}")
logger.info(f"batch_array_idx: {batch_array_idx}")

# write_to_dynamodb(batch_job_id, batch_array_idx, False, False)

session = Session()
session.add_combatant(Bugbear, Teams.Color.RED)
session.add_combatant(DragonclawCultist, Teams.Color.BLUE)
session.set_num_simulations(1)
try:
    result = session.simulate(parallel=False)
    s3_object_key = subdirectory + f'{"blue" if result[Teams.Color.BLUE] else "red"}_victory_log.txt'
    s3.upload_file(local_file_path, bucket_name, s3_object_key)
    # write_to_dynamodb(batch_job_id, batch_array_idx, True, False, result[Teams.Color.BLUE], result[Teams.Color.RED])
    logger.info(f"{batch_job_id}:{batch_array_idx} SUCCESS")
except Exception:
    # write_to_dynamodb(batch_job_id, batch_array_idx, True, True)
    logger.info(f"{batch_job_id}:{batch_array_idx} FAILURE")
    exit(1)
