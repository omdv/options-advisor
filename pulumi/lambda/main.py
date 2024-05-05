"""
Lambda to update S3 bucket contents
"""

import os
import datetime as dt
import boto3


def handler(event, context):
    """
    Lambda handler
    """

    # Read file_name and bucket_name from environment variables
    file_name = os.environ.get('FILE_NAME')
    bucket_name = os.environ.get('BUCKET_NAME')

    # Create an S3 client
    s3_client = boto3.client('s3')

    # Read the file from S3 bucket
    response = s3_client.get_object(Bucket=bucket_name, Key=file_name)
    file_content = response['Body'].read().decode('utf-8')

    # Check if the file is an HTML file
    if file_name.endswith('.html'):
        # Append text within the body of the HTML file
        updated_content = file_content.replace(
            'Last updated:',
            f'Last updated: {dt.datetime.now().strftime("%Y-%m-%d")}')

    # Write the updated file back to S3 bucket
    s3_client.put_object(
        Body=updated_content,
        Bucket=bucket_name,
        Key=file_name,
        ContentType='text/html; charset=utf-8')

    return {
        'statusCode': 200,
        'body': 'File updated successfully'
    }
