"""
Utility functions for reading and writing files.
"""

import os
import boto3

def save_to_s3(content, filename):
    """
    Save the content to an S3 bucket
    """
    # Read the bucket name from the environment variable
    bucket_name = os.environ.get('S3_BUCKET_NAME')

    # Create an S3 client
    s3 = boto3.client('s3')

    # Upload the content to the S3 bucket
    s3.put_object(
        Body=content,
        Bucket=bucket_name,
        Key=filename)


def read_from_s3(filename):
    """
    Read a file from an S3 bucket
    """
    # Read the bucket name from the environment variable
    bucket_name = os.environ.get('S3_BUCKET_NAME')

    # Create an S3 client
    s3 = boto3.client('s3')

    # Download the file from the S3 bucket
    response = s3.get_object(
        Bucket=bucket_name,
        Key=filename)

    # Read the file contents
    file_contents = response['Body'].read()

    return file_contents
