import boto3
import logging
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

logger = logging.getLogger("Encounterra")

dynamodb_resource = boto3.resource("dynamodb")
users_results_table = dynamodb_resource.Table("users")


def get_user_by_email(email):
    """
    Queries for users by email.

    :param email: The email to query.
    :return: The one user with that user_id.
    """
    try:
        response = users_results_table.query(KeyConditionExpression=Key('email').eq(email))
    except ClientError as err:
        logger.error(
            "Couldn't query for the user %s. Here's why: %s: %s", email,
            err.response['Error']['Code'], err.response['Error']['Message'])
        raise
    else:
        ret = response['Items']
        assert len(ret) == 1
        return ret[0]


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
    logger.info(f"event {event}")
    email = event["email"]
    initial_credits = event["initial_credits"]

    try:
        user_data = get_user_by_email(email)
        user_credits = user_data["credits"]
        if user_credits != -1:
            refresh_credits(email, initial_credits)
    except Exception as e:
        logger.error(f"Refreshing credits for {email} failed: {e}")
        exit(1)
