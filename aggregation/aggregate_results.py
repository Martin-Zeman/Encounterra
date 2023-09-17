import boto3
import argparse
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger("Encounterra")

dynamodb_resource = boto3.resource("dynamodb")
table = dynamodb_resource.Table("simulation_results")
s3 = boto3.client('s3')
bucket_name = "encounterra-simulation-results"
local_file_path = "/tmp/aggregated_statistics.txt"

def update_simulation_result(job_id: str,  s3_url: str, stats: str, success: bool):
    try:
        table.update_item(
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

def handler(event, context):
    logger.setLevel(logging.INFO)
    logger.info("------AGGREGATION LAMBDA STARTING------")
    logger.info(f"event {event}")
    results_array = event["core_results"]
    job_id = event["job_id"]

    total_blue_victories = 0
    total_red_victories = 0

    # Iterate over the results array and aggregate the victories
    for result in results_array:
        total_blue_victories += result.get('blue_victory', 0)
        total_red_victories += result.get('red_victory', 0)

    s3_url = f"https://encounterra-simulation-results.s3.eu-west-1.amazonaws.com/{job_id}"

    try:
        with open(local_file_path, 'w') as stats_file:
            stats_file.write(f"BLUE {total_blue_victories}\nRED {total_red_victories}\n")
        s3_object_key = f"{job_id}/aggregated_statistics.txt"
        s3.upload_file(local_file_path, bucket_name, s3_object_key)
        update_simulation_result(job_id, s3_url, f"BLUE: {total_blue_victories}, RED: {total_red_victories}", True)
        return {
            "final_result": {
                'total_blue_victories': total_blue_victories,
                'total_red_victories': total_red_victories
            }
        }
    except Exception as e:
        logger.error(f"Aggregation job for {job_id} failed: {e}")
        update_simulation_result(job_id, s3_url, f"BLUE: {total_blue_victories}, RED: {total_red_victories}", False)
        exit(1)
