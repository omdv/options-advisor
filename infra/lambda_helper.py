"""Lambda related functions."""
import os
from datetime import datetime as dt

import pulumi
import pulumi_aws as aws
import pulumi_docker as docker

def setup_ecr_repo():
  """Set up ECR repository."""
  # Create an ECR repository to store the Lambda function's Docker image.
  repo = aws.ecr.Repository(
    "lambda-repo",
    image_tag_mutability="IMMUTABLE",
  )

  # Create a new ECR lifecycle policy to remove untagged images after 7 days.
  _ = aws.ecr.LifecyclePolicy("lambda-lifecycle-policy",
    repository=repo.name,
    policy="""{
      "rules": [
      {
        "rulePriority": 1,
        "description": "Keep only last 5 images",
        "selection": {
          "tagStatus": "tagged",
          "tagPrefixList": ["v"],
          "countType": "imageCountMoreThan",
          "countNumber": 5
        },
        "action": {
          "type": "expire"
        }
      }
      ]
    }""",
  )
  return repo


def setup_lambda_image(repo):
    """Tag local docker image and upload to ECR."""
    version = os.environ.get("LAMBDA_VERSION", f'v{dt.now().strftime("%Y%m%d%H%M%S")}')
    # Get the login credentials for our Docker registry (ECR)
    auth_token = aws.ecr.get_authorization_token_output(registry_id=repo.registry_id)

    my_app_image = docker.Image("lambda-image",
        build=docker.DockerBuildArgs(
            context="lambda/",
            dockerfile="lambda/Dockerfile",
            platform="linux/amd64"
        ),
        image_name=repo.repository_url.apply(
            lambda repository_url: f"{repository_url}:{version}"
        ),
        registry=docker.RegistryArgs(
            username="AWS",
            password=pulumi.Output.secret(auth_token.password),
            server=repo.repository_url
        ))
    pulumi.export("imageName", my_app_image.image_name)
    return my_app_image


def setup_lambda(
        lambda_image: aws.lambda_.Function,
        website_bucket: aws.s3.Bucket,
    ) -> aws.lambda_.Function:
    """Set up roles and lambda function."""
    # Create an IAM role and policy that grants the necessary permissions to the Lambda function.
    lambda_role = aws.iam.Role("lambda-role",
        assume_role_policy=aws.iam.get_policy_document(
            statements=[aws.iam.GetPolicyDocumentStatementArgs(
                actions=["sts:AssumeRole"],
                effect="Allow",
                principals=[aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                    type="Service",
                    identifiers=["lambda.amazonaws.com"],
                )],
            )],
        ).json,
    )

    # Define a policy that allows the lambda to modify the website's S3 bucket.
    _ = aws.iam.RolePolicy("lambda-policy",
        role=lambda_role.id,
        policy=website_bucket.arn.apply(
            lambda arn: aws.iam.get_policy_document(
                statements=[aws.iam.GetPolicyDocumentStatementArgs(
                    actions=[
                        "s3:GetObject",
                        "s3:PutObject",
                    ],
                    resources=[arn + "/*"],
                    effect="Allow",
                )],
            ).json),
    )

    # Create a new Lambda function from a Docker image on ECR.
    website_lambda = aws.lambda_.Function("lambda-function",
        package_type="Image",
        image_uri=lambda_image.image_name,
        role=lambda_role.arn,
        memory_size=1024,
        timeout=120,
        environment=aws.lambda_.FunctionEnvironmentArgs(
            variables={
                "MODE": "prod",
                "S3_BUCKET_NAME": website_bucket.id,
                "ITM_PICKLE_PATH": os.environ.get("ITM_PICKLE_PATH"),
                "QUOTES_API_KEY": os.environ.get("QUOTES_API_KEY"),
                "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
                "NTFY_TOPIC": os.environ.get("NTFY_TOPIC"),
            },
        ),
    )

    # Give the Lambda function permissions to be invoked.
    _ = aws.lambda_.Permission("lambda-permission-to-s3",
        action="lambda:InvokeFunction",
        function=website_lambda.name,
        principal="s3.amazonaws.com",
        source_arn=website_bucket.arn,
    )

    return website_lambda
