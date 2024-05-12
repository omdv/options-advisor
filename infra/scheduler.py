"""
Create schedule events
"""

import pulumi_aws as aws

def schedule_lambda(website_lambda):
    """
    Schedule the lambda to run daily
    """

    # Create a CloudWatch Event Rule to trigger the Lambda function on a schedule.
    schedule_rule = aws.cloudwatch.EventRule("scheduleRule",
        schedule_expression="cron(0 0 * * ? *)",  # Run every day at midnight UTC
    )

    # Add a target to the CloudWatch Event Rule that triggers the Lambda function.
    _ = aws.cloudwatch.EventTarget("scheduleTarget",
        rule=schedule_rule.name,
        arn=website_lambda.arn,
    )

    return None