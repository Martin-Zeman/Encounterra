#!/bin/bash

S3_BUCKET_NAME="numba-cache-bucket"

# Clear the contents of the S3 bucket
echo "Clearing contents of S3 bucket: $S3_BUCKET_NAME"
aws s3 rm s3://$S3_BUCKET_NAME --recursive

# Start a new container in detached mode to perform the extraction
CONTAINER_ID=$(docker run --platform linux/arm64 -d --entrypoint /bin/bash encounterra-core:misc_and_utils_numba)

# Wait briefly for the container to start and perform the extraction
sleep 2

# Extract the Numba cache directory from the container
docker cp $CONTAINER_ID:/tmp/numba_cache .

# Stop and remove the container
docker stop $CONTAINER_ID >/dev/null 2>&1

echo "Uploading Numba cache to S3 bucket: $S3_BUCKET_NAME"
aws s3 cp ./numba_cache s3://$S3_BUCKET_NAME --recursive

echo "Numba cache extracted successfully."
