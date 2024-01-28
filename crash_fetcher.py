import copy

import boto3
import argparse
import os
import re
from botocore.exceptions import NoCredentialsError


def extract_id(filename):
    match = re.search(r'(\d+)\.(pkl|txt)$', filename)
    if match:
        return match.group(1)
    return None


def list_latest_files(bucket_name, prefix=''):
    s3 = boto3.client('s3')
    paginator = s3.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

    latest_time = None
    latest_id = ''
    all_file_names = []

    for page in page_iterator:
        for obj in page['Contents']:
            file_time = obj['LastModified']
            file_name = obj['Key']
            all_file_names.append(file_name)
            if latest_time is None or file_time > latest_time:
                latest_time = file_time
                latest_id = extract_id(file_name)

    latest_files = {}
    for file_name in all_file_names:
        if latest_id in file_name:
            if file_name.endswith('.pkl') and 'battle_map_data' in file_name:
                latest_files['battle_map'] = file_name
            elif file_name.endswith('.pkl') and 'session' in file_name:
                latest_files['session'] = file_name
            elif file_name.endswith('.txt') and 'exception' in file_name:
                latest_files['exception'] = file_name

    return latest_files


def get_exception_content(file_path, crash_number):
    exception_content = f"\nCrash Number: {crash_number}"
    with open(file_path, 'r') as file:
        exception_content += "\nException content:\n"
        exception_content += file.read()
    return exception_content


def download_files(bucket_name, file_names, download_path, print_exception=False):
    s3 = boto3.resource('s3')
    crash_number = None

    exception_content = ''
    for file_type, file_name in file_names.items():
        if file_name:
            download_to = os.path.join(download_path, file_name.split('/')[-1])
            s3.Bucket(bucket_name).download_file(file_name, download_to)
            print(f"Downloaded {file_name} to {download_to}")

            if crash_number is None:
                match = re.search(r'_(\d+)\.', file_name)
                if match:
                    crash_number = match.group(1)

            if print_exception and file_type == 'exception':
                exception_content = get_exception_content(download_to, crash_number)
    print(exception_content)


def delete_files(bucket_name, identifier):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    deleted_files = []

    for obj in bucket.objects.all():
        if identifier in obj.key:
            obj.delete()
            deleted_files.append(obj.key)
            print(f"Deleted {obj.key}")

    if not deleted_files:
        print(f"No files found with identifier {identifier}")


def main():
    parser = argparse.ArgumentParser(description="S3 Bucket File Management Utility")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-d", "--download-path", type=str, help="Path to download the files")
    group.add_argument("-r", "--delete", type=str, help="Identifier to delete files")
    parser.add_argument("-p", "--print-exception", action="store_true", help="Print the content of exception.txt")

    args = parser.parse_args()

    bucket_name = 'encounterra-simulation-crashes'
    if args.download_path:
        latest_files = list_latest_files(bucket_name)

        if latest_files:
            download_files(bucket_name, latest_files, args.download_path, args.print_exception)

    if args.delete:
        delete_files(bucket_name, args.delete)


if __name__ == "__main__":
    try:
        main()
    except NoCredentialsError:
        print("AWS credentials not found.")
