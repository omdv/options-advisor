"""
Create schedule events
"""

import pulumi_aws as aws

def schedule_lambda(website_lambda):
    """
    Schedule the lambda to run daily
    """

    # Create a CloudWatch Event Rule to trigger the Lambda function on a schedule.
    schedule_rule = aws.cloudwatch.EventRule(
        "scheduleRule",
        schedule_expression="cron(0/30 * * * ? *)",
    )

    # Add a target to the CloudWatch Event Rule that triggers the Lambda function.
    _ = aws.cloudwatch.EventTarget("scheduleTarget",
        rule=schedule_rule.name,
        arn=website_lambda.arn,
    )

    # Give permission for the Event Rule to invoke the Lambda Function
    _ = aws.lambda_.Permission(
        "lambda_permission",
        action="lambda:InvokeFunction",
        function=website_lambda.name,
        principal="events.amazonaws.com",
        source_arn=schedule_rule.arn)

    return None
