import boto3
import argparse
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger("Encounterra")

dynamodb = boto3.client('dynamodb')
s3 = boto3.client('s3')
bucket_name = "encounterra-simulation-results"

def update_simulation_result(job_id: str,  s3_link: str, stats: str, success: bool):
    try:
        dynamodb.update_item(
            Key={
                'job_id': job_id
            },
            UpdateExpression="SET s3_link = :s3_link, stats = :stats, finished = :finished, success = :success",
            ExpressionAttributeValues={
                ":s3_link": s3_link,
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
iterations = args.iterations

blue_victories = 0
red_victories = 0
try:
    for i in range(iterations):
        subdirectory = f"{batch_job_id}/{i}/"
        response = s3.get_object(Bucket=bucket_name, Key=subdirectory + 'statistics.txt')
        content = response['Body'].read().decode('utf-8')
        lines = content.split('\n')
        for line in lines:
            color, victories = line.strip().split()
            victories = int(victories)
            if color == 'BLUE':
                blue_victories += victories
            elif color == 'RED':
                red_victories += victories

    local_file_path = "/tmp/aggregated_statistics.txt"
    s3_object_key = f"{batch_job_id}/aggregated_statistics.txt"
    s3.upload_file(local_file_path, bucket_name, s3_object_key)
    update_simulation_result(batch_job_id, "", f"BLUE: {blue_victories}, RED: {red_victories}", True)
except Exception:
    update_simulation_result(batch_job_id, "", f"BLUE: {blue_victories}, RED: {red_victories}", False)
    exit(1)
