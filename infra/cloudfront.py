"""
Cloudfront exposing static site hosted on S3
"""
import json
import pulumi
import pulumi_aws as aws

def setup_cloudfront(website_bucket):
    """
    Setting up cloudfront and permissions
    """

    # Create an Origin Access Identity (OAI) for our CloudFront distribution
    oai = aws.cloudfront.OriginAccessIdentity(
        'cloudfront-oai',
        comment='OAI for my static website')

    # Create a CloudFront distribution for the S3 bucket
    distribution = aws.cloudfront.Distribution(
        'cloudfront-distribution',
        origins=[
            aws.cloudfront.DistributionOriginArgs(
                origin_id=website_bucket.arn,
                domain_name=website_bucket.bucket_regional_domain_name,
                s3_origin_config=aws.cloudfront.DistributionOriginS3OriginConfigArgs(
                    origin_access_identity=oai.cloudfront_access_identity_path
                ),
            )],
        enabled=True,
        is_ipv6_enabled=True,
        comment='CloudFront distribution for my static website',
        default_root_object='index.html',
        default_cache_behavior=aws.cloudfront.DistributionDefaultCacheBehaviorArgs(
            allowed_methods=['GET', 'HEAD'],
            cached_methods=['GET', 'HEAD'],
            target_origin_id=website_bucket.arn,
            forwarded_values=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesArgs(
                query_string=False,
                cookies=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesCookiesArgs(forward='none') # pylint: disable=line-too-long
            ),
            viewer_protocol_policy='redirect-to-https',
            min_ttl=0,
            default_ttl=3600,
            max_ttl=86400,
        ),
        price_class='PriceClass_100',
        restrictions=aws.cloudfront.DistributionRestrictionsArgs(
            geo_restriction=aws.cloudfront.DistributionRestrictionsGeoRestrictionArgs(
                restriction_type='none'
            )
        ),
        viewer_certificate=aws.cloudfront.DistributionViewerCertificateArgs(
            cloudfront_default_certificate=True,
        ))

    bucket_policy = pulumi.Output.all(website_bucket.arn, oai.id).apply(
        lambda args: json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {
                    "AWS": f"arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity {args[1]}" # pylint: disable=line-too-long
                },
                "Action": "s3:GetObject",
                "Resource": f"{args[0]}/*"
            }]
        })
    )

    # Update the S3 bucket policy with the new policy JSON
    _ = aws.s3.BucketPolicy(
        "s3-bucket-policy",
        bucket=website_bucket.id,
        policy=bucket_policy
    )

    return distribution
