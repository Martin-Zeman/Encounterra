#!/bin/bash

declare -A ACCOUNT_NAME
declare -A ACCOUNT_NUMBER
declare -A ACCOUNT_ENVIRONMENT

ACCOUNT_NAME["test"]="test"
ACCOUNT_NUMBER["test"]="297945307580"
ACCOUNT_ENVIRONMENT["test"]="Test"

ACCOUNT_NAME["prod"]="prod"
ACCOUNT_NUMBER["prod"]="728464280382"
ACCOUNT_ENVIRONMENT["prod"]="Production"

# Prod
# arn:aws:iam::728464280382:user/admin
# AKIA2TG62ZM7KMHS3GNK
# SaoZXfYoH99srpwhKqPe+kcc8TOy+EkKbG9vTdFZ
# eu-west-1
# json
#
# Test
# arn:aws:iam::297945307580:user/admin_test
# AKIAUKXXMTG6OSXPBYEI
# q29iVq4aqGy9jcc6OwhtoJbU7jpXlJC2/Vm8Xego
# eu-west-1
# json

usage() {
  echo -e >&2 "
    assume.sh Assumes role for a target account.

    Sytnax: . assume.sh ACCOUNT

    ACCOUNT - Account name shorthand
    Available accounts: ${!ACCOUNT_NUMBER[@]}

    OPTIONS:
    <-h|--help>
  "
}

TEMP=$(getopt -o h --long help -- "$@")
eval set -- "$TEMP"

while true; do
  case "$1" in
    -h|--help) usage; return;;

    --) shift; break;;
    *) echo "Internal error!"; return 1;;
  esac
done

TARGET_ACCOUNT="$1"
TARGET_ACCOUNT_NR=${ACCOUNT_NUMBER[$TARGET_ACCOUNT]}
TARGET_ACCOUNT_NAME=${ACCOUNT_NAME[$TARGET_ACCOUNT]}
TARGET_ACCOUNT_ENVIRONMENT=${ACCOUNT_ENVIRONMENT[$TARGET_ACCOUNT]}
if [ -z "${TARGET_ACCOUNT}" ]; then
  usage
  return
fi
if [ -z "${TARGET_ACCOUNT_NR}" ]; then
  echo -e >&1 "
    Unknown account '${TARGET_ACCOUNT}'

    Available accounts: ${!ACCOUNT_NUMBER[@]}
  "
  return 1
fi

ASSUME_ROLE_FILE=$(mktemp)
ENV_FILE=$(mktemp)
echo "Assuming role for $TARGET_ACCOUNT_NAME ($TARGET_ACCOUNT_NR)..."
aws sts get-session-token --profile "$TARGET_ACCOUNT_NAME" --duration-seconds 900 > $ASSUME_ROLE_FILE || return 1

AWS_ACCESS_KEY_ID=$(jq -r .Credentials.AccessKeyId $ASSUME_ROLE_FILE)
AWS_SECRET_ACCESS_KEY=$(jq -r .Credentials.SecretAccessKey $ASSUME_ROLE_FILE)
AWS_SESSION_TOKEN=$(jq -r .Credentials.SessionToken $ASSUME_ROLE_FILE)

echo 'export AWS_ACCESS_KEY_ID="'$AWS_ACCESS_KEY_ID'"' >> $ENV_FILE
echo 'export AWS_SECRET_ACCESS_KEY="'$AWS_SECRET_ACCESS_KEY'"' >> $ENV_FILE
echo 'export AWS_SESSION_TOKEN="'$AWS_SESSION_TOKEN'"' >> $ENV_FILE
echo 'export AWS_ENVIRONMENT="'$TARGET_ACCOUNT_ENVIRONMENT'"' >> $ENV_FILE

source $ENV_FILE

echo "done"

PS1="\033[33m$TARGET_ACCOUNT-assumed\033[00m $PS1"

rm -f $ASSUME_ROLE_FILE
rm -f $ENV_FILE