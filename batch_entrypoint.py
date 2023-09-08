from simulator.combatants.bugbear import Bugbear
from simulator.logging.custom_logger import CustomLogger, LogLevel
from simulator.session import Session
from simulator.combatants.dragonclaw_cultist import DragonclawCultist
from simulator.teams import Teams

import boto3
import argparse
import logging
from botocore.exceptions import ClientError

def write_to_dynamodb(session_uuid: str, iteration: int, finished: bool, failed: bool, blue_victories=0, red_victories=0):
    try:
        response = dynamodb.put_item(
            TableName=table_name,
            Item={
                'session_uuid': {'S': session_uuid},
                'iteration': {'N': str(iteration)},
                'finished': {'BOOL': finished},
                'failed': {'BOOL': failed},
                'blue_victories': {'N': str(blue_victories)},
                'red_victories': {'N': str(red_victories)},
            }
        )
        return response
    except ClientError as e:
        print(e)
        return None

dynamodb = boto3.client('dynamodb')
table_name = 'simulation_tracking'
CustomLogger(LogLevel.INFO)
logger = logging.getLogger("Encounterra")
logger.info("------CORE BATCH JOB STARTING------")

parser = argparse.ArgumentParser()

parser.add_argument('--session-uuid', type=str)
parser.add_argument('--iteration', type=int)
# parser.add_argument('--list-arg', nargs='+', type=str, help='A list of strings')
args = parser.parse_args()

session_uuid = args.session_uuid
iteration = args.iteration
logger.info(f"session_uuid: {session_uuid}")
logger.info(f"iteration: {iteration}")

write_to_dynamodb(session_uuid, iteration, False, False)

session = Session()
session.add_combatant(Bugbear, Teams.Color.RED)
session.add_combatant(DragonclawCultist, Teams.Color.BLUE)
session.set_num_simulations(1)
try:
    result = session.simulate(parallel=False)
    write_to_dynamodb(session_uuid, iteration, True, False, result[Teams.Color.BLUE], result[Teams.Color.RED])
    logger.info(f"{session_uuid}:{iteration} SUCCESS")
except Exception:
    write_to_dynamodb(session_uuid, iteration, True, True)
    logger.info(f"{session_uuid}:{iteration} FAILURE")
