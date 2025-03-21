"""An AWS Python Pulumi program"""

import os
import pulumi_aws as aws
import pulumi

import s3_helper as s3h
import lambda_helper as lmh
import lambda_schedule as sch
import cloudfront as cf
import route53 as r53

# Configure the AWS region to deploy resources into.
aws.config.region = os.environ.get("AWS_REGION", "us-east-1")

# Create an S3 bucket to store the static website files.
website_bucket = s3h.create_bucket()
s3h.upload_files(website_bucket)

# Setup the Lambda function to process the website files.
ecr_repo = lmh.setup_ecr_repo()
lambda_image = lmh.setup_lambda_image(ecr_repo)
website_lambda = lmh.setup_lambda(lambda_image, website_bucket)

# Setup scheduler
sch.schedule_lambda(website_lambda)

# Setup CloudFront
distribution = cf.setup_cloudfront(website_bucket)

# Setup ACM
r53.setup_dns(distribution)

# Export the variables
pulumi.export("S3 bucket", website_bucket.bucket)
pulumi.export("Website URL", website_bucket.website_endpoint)
pulumi.export("Lambda image", lambda_image.image_name)
pulumi.export("CloudFront domain", distribution.domain_name)
