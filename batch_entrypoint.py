from simulator.combatants.bugbear import Bugbear
from simulator.logging.custom_logger import CustomLogger, LogLevel
from simulator.session import Session
from simulator.combatants.dragonclaw_cultist import DragonclawCultist
from simulator.teams import Teams

import boto3
import argparse
from botocore.exceptions import ClientError

dynamodb = boto3.client('dynamodb')
table_name = 'simulation_tracking'

def write_to_dynamodb(session_uuid: str, iteration: str, finished: bool, failed: bool, blue_victories=0, red_victories=0):
    try:
        response = dynamodb.put_item(
            TableName=table_name,
            Item={
                'session_uuid': {'S': session_uuid},
                'iteration': {'N': iteration},
                'finished': {'BOOL': finished},
                'failed': {'BOOL': failed},
                'blue_victories': {'N': blue_victories},
                'red_victories': {'N': red_victories},
            }
        )
        return response
    except ClientError as e:
        print(e)
        return None


parser = argparse.ArgumentParser()

parser.add_argument('--session-uuid', type=str)
parser.add_argument('--iteration', type=int)
# parser.add_argument('--list-arg', nargs='+', type=str, help='A list of strings')
args = parser.parse_args()

session_uuid = args.session_uuid
iteration = args.iteration

write_to_dynamodb(session_uuid, iteration, False, False)

CustomLogger(LogLevel.INFO)
session = Session()
session.add_combatant(Bugbear, Teams.Color.RED)
session.add_combatant(DragonclawCultist, Teams.Color.BLUE)
session.set_num_simulations(1)
try:
    result = session.simulate(parallel=False)
    write_to_dynamodb(session_uuid, iteration, True, False, result[Teams.Color.BLUE], result[Teams.Color.RED])
except Exception:
    write_to_dynamodb(session_uuid, iteration, True, True)
