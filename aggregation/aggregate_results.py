import boto3
import argparse
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger("Encounterra")

dynamodb_resource = boto3.resource("dynamodb")
table = dynamodb_resource.Table("simulation_results")
s3 = boto3.client('s3')
bucket_name = "encounterra-simulation-results"

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


parser = argparse.ArgumentParser()

parser.add_argument('--batch-job-id', type=str)
parser.add_argument('--iterations', type=str)
args = parser.parse_args()
batch_job_id = args.batch_job_id
iterations = int(args.iterations)
s3_url = f"https://encounterra-simulation-results.s3.eu-west-1.amazonaws.com/{batch_job_id}"

blue_victories = 0
red_victories = 0
try:
    for i in range(iterations):
        subdirectory = f"{batch_job_id}/{i}/"
        response = s3.get_object(Bucket=bucket_name, Key=subdirectory + 'statistics.txt')
        content = response['Body'].read().decode('utf-8')
        lines = content.split('\n')[:-1]   # Excludes the last empty line
        for line in lines:
            color, victories = line.strip().split()
            victories = int(victories)
            if color == 'BLUE':
                blue_victories += victories
            elif color == 'RED':
                red_victories += victories

    local_file_path = "/tmp/aggregated_statistics.txt"
    with open(local_file_path, 'w') as stats_file:
        stats_file.write(f"BLUE {blue_victories}\nRED {red_victories}\n")
    s3_object_key = f"{batch_job_id}/aggregated_statistics.txt"
    s3.upload_file(local_file_path, bucket_name, s3_object_key)
    update_simulation_result(batch_job_id, s3_url, f"BLUE: {blue_victories}, RED: {red_victories}", True)
except Exception as e:
    logger.error(f"Aggregation job for {batch_job_id} failed: {e}")
    update_simulation_result(batch_job_id, s3_url, f"BLUE: {blue_victories}, RED: {red_victories}", False)
    exit(1)
