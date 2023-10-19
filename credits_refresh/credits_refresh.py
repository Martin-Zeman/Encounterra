import boto3
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger("Encounterra")

dynamodb_resource = boto3.resource("dynamodb")
users_results_table = dynamodb_resource.Table("users")


def refresh_credits(email: str, initial_credits: int):

    try:
        users_results_table.update_item(
            Key={
                "email": email
            },
            UpdateExpression="SET credits = :initial_credits",
            ExpressionAttributeValues={
                ":initial_credits": initial_credits
            },
            ReturnValues="UPDATED_NEW")
    except ClientError as err:
        logger.error(
            "Couldn't update the credits for user %s from table users. Here's why: %s: %s",
            email,
            err.response['Error']['Code'], err.response['Error']['Message'])
        raise


def handler(event, context):
    logger.setLevel(logging.INFO)
    logger.info("------CREDIT REFRESH LAMBDA STARTING------")
    logger.info(f"event {event}")
    email = event["email"]
    initial_credits = event["initial_credits"]

    try:
        refresh_credits(email, initial_credits)
    except Exception as e:
        logger.error(f"Refreshing credits for {email} failed: {e}")
        exit(1)
