#!/bin/bash

# Set your AWS region
REGION="eu-west-1"

# DynamoDB table name
TABLE_NAME="users"

# Fetch user_ids from DynamoDB table
USER_IDS=$(aws dynamodb scan --table-name $TABLE_NAME --projection-expression "user_id" --region $REGION | jq -r '.Items[].user_id.S')

# List EventBridge rules
RULES=$(aws events list-rules --region $REGION | jq -r '.Rules[].Name')

# Loop through each rule
for rule in $RULES; do
    match_found=false

    # Check if rule name starts with any user_id
    for user_id in $USER_IDS; do
        if [[ $rule == $user_id* ]]; then
            match_found=true
            break
        fi
    done

    # Disable rule if no matching user_id is found
    if [ "$match_found" = false ]; then
        echo "Disabling rule: $rule"
        aws events disable-rule --name "$rule" --region $REGION
    fi
done
