"""An AWS Python Pulumi program"""

import os
import json
import random
import pulumi_aws as aws
import pulumi

# Local resources
S3_LOCAL_DIR = "./s3"
S3_KEY_PREFIX = "/"
LOCAL_LAMBDA_FILE = "./lambda/lambda.zip"
S3_LAMBDA_KEY = "lambda.zip"

# Configure the AWS region to deploy resources into.
aws.config.region = "us-east-1"

# Create random 12 character string for the bucket name.
def random_suffix():
    """
    Generate a random 12 character string.
    """
    return "".join(random.choices("abcdefghijklmnopqrstuvwxyz1234567890", k=12))


# Create an S3 bucket without a "public-read" ACL.
website_bucket = aws.s3.Bucket("websiteBucket",
    website=aws.s3.BucketWebsiteArgs(
        index_document="index.html",
    ),
    bucket=os.environ.get("S3_BUCKET_NAME", f"options-advisor-{random_suffix()}")
)

# Allow public access
example_bucket_public_access_block = aws.s3.BucketPublicAccessBlock(
    "allowPublicAccess",
    bucket=website_bucket.id,
    block_public_policy=False)


# Define the public read policy for the bucket.
public_read_policy = website_bucket.arn.apply(
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
bucket_policy = aws.s3.BucketPolicy("bucketPolicy",
    bucket=website_bucket.id,
    policy=public_read_policy
)

# Iterate over the files in the directory
for root, dirs, files in os.walk(S3_LOCAL_DIR):
    for filename in files:
        # Construct the local file path
        local_path = os.path.join(root, filename)

        # Construct the S3 key
        s3_key = os.path.join(
            S3_KEY_PREFIX,
            os.path.relpath(local_path, S3_LOCAL_DIR))

        # Create a BucketObject for the file
        file_object = aws.s3.BucketObject(s3_key,
            bucket=website_bucket.id,
            source=pulumi.FileAsset(local_path),
            opts=pulumi.ResourceOptions(parent=website_bucket)
        )


# Create an IAM role and policy that grants the necessary permissions to the Lambda function.
lambda_role = aws.iam.Role("lambdaRole",
    assume_role_policy=aws.iam.get_policy_document(
        statements=[aws.iam.GetPolicyDocumentStatementArgs(
            actions=["sts:AssumeRole"],
            effect="Allow",
            principals=[aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                type="Service",
                identifiers=["lambda.amazonaws.com"],
            )],
        )]
    ).json,
)

# Define a policy that allows the lambda to modify the website's S3 bucket.
lambda_policy = aws.iam.RolePolicy("lambdaPolicy",
    role=lambda_role.id,
    policy=website_bucket.arn.apply(
        lambda arn: aws.iam.get_policy_document(
            statements=[aws.iam.GetPolicyDocumentStatementArgs(
                actions=["s3:GetObject", "s3:PutObject"],
                resources=[arn + "/*"],
                effect="Allow",
            )]
        ).json),
)

# Upload lambda code to s3.
lambda_archive = aws.s3.BucketObject("lambda_archive",
    bucket=website_bucket.id,
    source=pulumi.FileAsset(LOCAL_LAMBDA_FILE),
    key=S3_LAMBDA_KEY
)

# Define the Lambda function that can modify website contents.
website_lambda = aws.lambda_.Function("websiteLambda",
    s3_bucket=website_bucket.id,
    s3_key="lambda.zip",
    handler="main.handler",
    role=lambda_role.arn,
    runtime="python3.8",
    environment=aws.lambda_.FunctionEnvironmentArgs(
        variables={
            "S3_BUCKET_NAME": website_bucket.id,
            "FILE_NAME": "index.html",
        }
    )
)

# Give the Lambda function permissions to be invoked.
lambda_permission = aws.lambda_.Permission("lambdaPermission",
    action="lambda:InvokeFunction",
    function=website_lambda.name,
    principal="s3.amazonaws.com",
    source_arn=website_bucket.arn,
)

# Create a CloudWatch Event Rule to trigger the Lambda function on a schedule.
schedule_rule = aws.cloudwatch.EventRule("scheduleRule",
    schedule_expression="cron(0 0 * * ? *)",  # Run every day at midnight UTC
)

# Add a target to the CloudWatch Event Rule that triggers the Lambda function.
schedule_target = aws.cloudwatch.EventTarget("scheduleTarget",
    rule=schedule_rule.name,
    arn=website_lambda.arn,
)

# Export the website URL to access the static website.
pulumi.export("website_url", website_bucket.website_endpoint)
