"""
Function for s3 handling
"""
import os
import json
import pulumi
import pulumi_aws as aws

# Local resources
S3_LOCAL_DIR = "./s3"
S3_KEY_PREFIX = "/"

def create_bucket():
    """
    Create and configure s3 bucket
    """

    # Create an S3 bucket to store the static website files.
    website_bucket = aws.s3.Bucket(
        "s3-bucket",
        website=aws.s3.BucketWebsiteArgs(index_document="index.html"))

    # Block public access
    _ = aws.s3.BucketPublicAccessBlock(
        "s3-block-public-access",
        bucket=website_bucket.id,
        block_public_acls=True,
        block_public_policy=True,
        ignore_public_acls=True,
        restrict_public_buckets=True,
    )

    return website_bucket

def upload_files(website_bucket):
    """
    Upload files to the S3 bucket.
    """
    for root, _, files in os.walk(S3_LOCAL_DIR):
        for filename in files:
            # Construct the local file path
            local_path = os.path.join(root, filename)

            # Construct the S3 key
            s3_key = os.path.join(
                S3_KEY_PREFIX,
                os.path.relpath(local_path, S3_LOCAL_DIR))

            if filename.endswith(".css"):
                content_type = "text/css"
            else:
                content_type = None

            # Create a BucketObject for the file
            _ = aws.s3.BucketObject(s3_key,
                bucket=website_bucket.id,
                source=pulumi.FileAsset(local_path),
                content_type=content_type,
                opts=pulumi.ResourceOptions(parent=website_bucket)
            )

    return None
