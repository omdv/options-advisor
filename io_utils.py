"""
Utility functions for reading and writing files.
"""
import boto3

def save_to_s3(config, filename, content, content_type=None):
    """
    Save the content to an S3 bucket
    """

    # Upload the content to the S3 bucket
    if config['mode'] == 'dev':
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
    elif config['mode'] == 'prod':
        s3 = boto3.client('s3')
        s3.put_object(
            Body=content,
            Bucket=config['bucket_name'],
            Key=filename,
            ContentType=content_type)


def read_from_s3(config, filename, decode=False):
    """
    Read a file from an S3 bucket
    """

    if config['mode'] == 'dev':
        with open(filename, 'rb') as f:
            file_contents = f.read()
    elif config['mode'] == 'prod':
        s3 = boto3.client('s3')
        response = s3.get_object(
            Bucket=config['bucket_name'],
            Key=filename)
        file_contents = response['Body'].read()

    if decode:
        file_contents = file_contents.decode('utf-8')

    return file_contents
