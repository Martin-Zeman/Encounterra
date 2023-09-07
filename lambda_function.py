from simulator.combatants.bugbear import Bugbear
from simulator.logging.custom_logger import CustomLogger, LogLevel
from simulator.session import Session
from simulator.combatants.dragonclaw_cultist import DragonclawCultist
from simulator.teams import Teams

import boto3
from botocore.exceptions import ClientError

# Initialize DynamoDB client
dynamodb = boto3.client('dynamodb')
table_name = 'simulation_tracking'

def write_to_dynamodb(session_uuid: str, iteration: str, finished: bool):
    try:
        response = dynamodb.put_item(
            TableName=table_name,
            Item={
                'session_uuid': {'S': session_uuid},
                'iteration': {'N': iteration},
                'finished': {'BOOL': finished}
            }
        )
        return response
    except ClientError as e:
        print(e)
        return None


def handler(event, context):
    session_uuid = event['session_uuid']
    iteration = event['iteration']
    max_attempts = int(event['max_attempts'])

    write_to_dynamodb(session_uuid, iteration, finished=False)

    CustomLogger(LogLevel.INFO)
    session = Session()
    session.add_combatant(Bugbear, Teams.Color.RED)
    session.add_combatant(DragonclawCultist, Teams.Color.BLUE)
    session.set_num_simulations(1)
    failures = 0
    result = None
    while failures < max_attempts:
        try:
            result = session.simulate(parallel=False)
            break
        except Exception:
            failures += 1
    if failures < max_attempts:
        write_to_dynamodb(session_uuid, iteration, finished=True)
