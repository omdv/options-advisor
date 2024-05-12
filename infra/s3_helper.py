"""
Function for s3 handling
"""
import os
import json
import random
import pulumi
import pulumi_aws as aws

# Local resources
S3_LOCAL_DIR = "./s3"
S3_KEY_PREFIX = "/"

# Create random 12 character string for the bucket name.
def random_suffix():
    """
    Generate a random 12 character string.
    """
    return "".join(random.choices("abcdefghijklmnopqrstuvwxyz1234567890", k=12))

def create_bucket():
    """
    Create and configure s3 bucket
    """
    website_bucket = aws.s3.Bucket("websiteBucket",
        website=aws.s3.BucketWebsiteArgs(
            index_document="index.html",
        ),
        bucket=os.environ.get("AWS_S3_BUCKET", f"options-advisor-{random_suffix()}")
    )

    # Block public access
    _ = aws.s3.BucketPublicAccessBlock(
        "allowPublicAccess",
        bucket=website_bucket.id,
        block_public_acls=True,
        block_public_policy=True,
        ignore_public_acls=True,
        restrict_public_buckets=True,
    )


def public_read_policy(website_bucket):
    """
    Create a public read policy for the S3 bucket.
    """

    # Define the public read policy for the bucket.
    policy = website_bucket.arn.apply(
        lambda arn: json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": "*",
                "Action": ["s3:GetObject"],
                "Resource": [f"{arn}/*"]
            }]
        })
    )

    # Apply the public read policy to the bucket.
    _ = aws.s3.BucketPolicy("bucketPolicy",
        bucket=website_bucket.id,
        policy=policy
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
