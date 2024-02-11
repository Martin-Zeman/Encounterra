import boto3
import logging
import os
import zipfile
import json
from enum import Enum
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

logger = logging.getLogger("Encounterra")

dynamodb_resource = boto3.resource("dynamodb")
simulation_results_table = dynamodb_resource.Table("simulation_results")
users_results_table = dynamodb_resource.Table("users")
s3 = boto3.client('s3')
bucket_name = "encounterra-simulation-results"
aggregated_stats_path = "/tmp/aggregated_statistics.txt"

STANDARD_TEAM_SIZE = 4


class Statistics(Enum):
    VICTORIES = 1
    AT_LEAST_ONE_DIED = 2
    AT_LEAST_TWO_DIED = 3
    AT_LEAST_THREE_DIED = 4
    CLASSIFICATION = 5


def update_simulation_result(job_id: str,  s3_url: str, stats: str, success: bool):
    try:
        simulation_results_table.update_item(
            Key={
                'job_id': job_id
            },
            UpdateExpression="SET s3_url = :s3_url, stats = :stats, finished = :finished, success = :success",
            ExpressionAttributeValues={
                ":s3_url": s3_url,
                ":stats": stats,
                ":finished": True,
                ":success": success
            },
            ReturnValues="UPDATED_NEW")
    except ClientError as err:
        logger.error(
            "Couldn't update the %s simulation_results table. Here's why: %s: %s",
            job_id,
            err.response['Error']['Code'], err.response['Error']['Message'])
        raise


def get_iterations(job_id: str):
    try:
        response = simulation_results_table.get_item(
            Key={
                "job_id": job_id
            }
        )
        # Return the Item if it exists, otherwise return None
        return int(response['Item']['iterations'])
    except ClientError as err:
        logger.error(
            "Couldn't retrieve result for %s from table simulation_results. Here's why: %s: %s",
            job_id,
            err.response['Error']['Code'], err.response['Error']['Message'])
        raise


def get_email_by_user_id(user_id: str) -> str:
    """
    Queries for user's email by user_id using the GSI.

    :param user_id: The user_id to query.
    :return: The email associated with the user_id.
    """
    table = users_results_table
    response = table.query(
        IndexName="UserIdIndex",
        KeyConditionExpression=Key('user_id').eq(user_id)
    )
    items = response['Items']
    if not items:
        raise ValueError(f"No user found with user_id {user_id}")
    return items[0]['email']


def update_credits(user_id: str, credits_to_deduct: int):
    email = get_email_by_user_id(user_id)

    try:
        users_results_table.update_item(
            Key={
                "email": email
            },
            UpdateExpression="ADD credits :neg_credits",
            ExpressionAttributeValues={
                ":neg_credits": -credits_to_deduct
            },
            ReturnValues="UPDATED_NEW")
    except ClientError as err:
        logger.error(
            "Couldn't update the credits for user %s from table users. Here's why: %s: %s",
            user_id,
            err.response['Error']['Code'], err.response['Error']['Message'])
        raise


def zip_s3_bucket_objects_and_get_presigned_url(bckt_name, job_id, aggr_stats_path):
    # Define the local zip path and the s3 zip object key
    local_zip_path = "/tmp/results.zip"
    s3_zip_object_key = f"{job_id}/results.zip"

    # List all objects under the specified prefix
    objects = s3.list_objects_v2(Bucket=bckt_name, Prefix=job_id)

    # Create a zip file and add the S3 objects to it
    with zipfile.ZipFile(local_zip_path, 'w') as zf:
        # Add aggregated statistics file without iteration number
        zf.write(aggr_stats_path, arcname=os.path.basename(aggr_stats_path))

        for obj in objects.get('Contents', []):
            object_key = obj['Key']
            local_file_path = f"/tmp/{os.path.basename(object_key)}"

            # Extract iteration number from object key (assuming the format 'iteration_number/filename')
            iteration_number = object_key.split('/')[1]  # Adjust index based on your object key format

            # Download the object to a local file
            s3.download_file(bckt_name, object_key, local_file_path)

            # Add the object to the zip file with iteration number prepended to its filename
            modified_filename = f"{iteration_number}_{os.path.basename(object_key)}"
            zf.write(local_file_path, arcname=modified_filename)

            # Optional: remove the temporary local file after adding to zip (to free up space)
            os.remove(local_file_path)

    # Upload the zip file to S3
    s3.upload_file(local_zip_path, bckt_name, s3_zip_object_key)

    # Generate a presigned URL for the zip file
    s3_url = s3.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': bckt_name,
            'Key': s3_zip_object_key
        },
        ExpiresIn=86400
    )

    return s3_url


def classify_encounter(difficulty_statistics, total_iterations, team_size):
    classification = "Easy"
    team_size_modifier = team_size / STANDARD_TEAM_SIZE

    for color, stats in difficulty_statistics.items():
        victories = stats[Statistics.VICTORIES.name]
        total_deaths = (
                stats[Statistics.AT_LEAST_ONE_DIED.name] +
                stats[Statistics.AT_LEAST_TWO_DIED.name] +
                stats[Statistics.AT_LEAST_THREE_DIED.name]
        )

        at_least_one_died_percentage = stats[Statistics.AT_LEAST_ONE_DIED.name] / total_iterations * team_size_modifier
        at_least_two_died_percentage = stats[Statistics.AT_LEAST_TWO_DIED.name] / total_iterations * team_size_modifier

        if victories == total_iterations:
            if total_deaths == 0:
                classification = "Easy"
            elif at_least_one_died_percentage <= 0.2:
                classification = "Medium"
            else:
                classification = "Hard"
        else:
            if at_least_two_died_percentage <= 0.4:
                classification = "Hard"
            else:
                classification = "Deadly"

    return classification


def handler(event, context):
    logger.setLevel(logging.INFO)
    logger.info("------AGGREGATION LAMBDA STARTING------")
    logger.info(f"event {event}")
    results_array = event["core_results"]
    job_id = event["job_id"]
    user_id = event["user_id"]
    credit_cost = event["credit_cost"]
    logger.info(f"MY DEBUG core_input: {event['core_input']}")
    logger.info(f"MY DEBUG core_input[0]: {event['core_input'][0]}")
    blue_team_size = len(event['core_input'][0]['blue'])
    red_team_size = len(event['core_input'][0]['red'])

    iterations = get_iterations(job_id)
    if iterations != len(results_array):
        logger.error(f"Some iterations failed despite retries!")
        exit(1)

    statistics = {color: {stat.name: 0 for stat in Statistics} for color in ['BLUE', 'RED']}

    # Iterate over the results array and aggregate the victories
    for result in results_array:
        statistics['BLUE'][Statistics.VICTORIES.name] += result.get('blue_victory', 0)
        statistics['RED'][Statistics.VICTORIES.name] += result.get('red_victory', 0)
        statistics['BLUE'][Statistics.AT_LEAST_ONE_DIED.name] += result.get('blue_at_least_one_died', 0)
        statistics['RED'][Statistics.AT_LEAST_ONE_DIED.name] += result.get('red_at_least_one_died', 0)
        statistics['BLUE'][Statistics.AT_LEAST_TWO_DIED.name] += result.get('blue_at_least_two_died', 0)
        statistics['RED'][Statistics.AT_LEAST_TWO_DIED.name] += result.get('red_at_least_two_died', 0)
        statistics['BLUE'][Statistics.AT_LEAST_THREE_DIED.name] += result.get('blue_at_least_three_died', 0)
        statistics['RED'][Statistics.AT_LEAST_THREE_DIED.name] += result.get('red_at_least_three_died', 0)

    blue_classification = classify_encounter(statistics, iterations, blue_team_size)
    statistics['BLUE'][Statistics.CLASSIFICATION.name] = blue_classification['BLUE']
    red_classification = classify_encounter(statistics, iterations, red_team_size)
    statistics['RED'][Statistics.CLASSIFICATION.name] = red_classification['RED']

    statistics = json.dumps(statistics)

    try:
        with open(aggregated_stats_path, 'w') as stats_file:
            stats_file.write(statistics)
        s3_url = zip_s3_bucket_objects_and_get_presigned_url(bucket_name, job_id, aggregated_stats_path)

        if credit_cost > 0:
            update_credits(user_id, iterations)

        update_simulation_result(job_id, s3_url, statistics, True)
    except Exception as e:
        logger.error(f"Aggregation job for {job_id} failed: {e}")
        s3_url = f"https://encounterra-simulation-results.s3.eu-west-1.amazonaws.com/{job_id}"
        update_simulation_result(job_id, s3_url, statistics, False)
        exit(1)
