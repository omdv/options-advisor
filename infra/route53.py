"""
Setup dns and route53
"""

import os
import pulumi
import pulumi_aws as aws

def setup_dns(distribution):
    """
    DNS related functions
    """

    my_domain_name = os.environ.get("DOMAIN_NAME")

    # Create a Route 53 zone for the domain
    hosted_zone = aws.route53.Zone(
        "my-domain-zone",
        name=my_domain_name
    )

    # Create an alias record for the CloudFront distribution
    _ = aws.route53.Record(
        "my-alias-record",
        zone_id=hosted_zone.id,
        name=my_domain_name,
        type="A",
        aliases=[
            aws.route53.RecordAliasArgs(
                name=distribution.domain_name,
                zone_id="Z2FDTNDATAQYW2", # This is the fixed CloudFront zone ID
                evaluate_target_health=False,
            )]
    )

    # Request an ACM certificate for the domain and alternate domain name
    certificate = aws.acm.Certificate("my-certificate",
        domain_name=my_domain_name,
        validation_method="DNS"
    )

    # Retrieve the validation options
    certificate_validation_options = certificate.domain_validation_options

    # Create Route 53 DNS records for validation
    validation_records = []
    def create_validation_records(options):
        for option in options:
            validation_record = aws.route53.Record(f"validationRecord-{option.domain_name}",
                name=option.resource_record_name,
                zone_id=hosted_zone.zone_id,
                type=option.resource_record_type,
                records=[option.resource_record_value],
                ttl=300
            )
            validation_records.append(validation_record)

    certificate_validation_options.apply(create_validation_records)

    # Validate the ACM certificate
    _ = aws.acm.CertificateValidation(
        "certificate-validation",
        certificate_arn=certificate.arn,
        validation_record_fqdns=pulumi.Output.all(*validation_records).apply(
            lambda records: [record.fqdn for record in records]
        )
    )

    # Function to update the CloudFront distribution with new properties
    def update_distribution(existing_distribution, certificate_arn):
        return aws.cloudfront.Distribution(
            "updated-cloudfront-distribution",
            origins=existing_distribution.origins.apply(lambda origins: [{
                "domain_name": origin["domain_name"],
                "origin_id": origin["origin_id"],
                "s3_origin_config": origin.get("s3_origin_config"),
                "custom_origin_config": origin.get("custom_origin_config")
            } for origin in origins]),
            enabled=True,
            is_ipv6_enabled=True,
            default_cache_behavior=existing_distribution.default_cache_behavior.apply(lambda cb: {
                "targetOriginId": cb["target_origin_id"],
                "viewerProtocolPolicy": cb["viewer_protocol_policy"],
                "allowedMethods": cb["allowed_methods"],
                "cachedMethods": cb["cached_methods"],
                "forwardedValues": cb["forwarded_values"],
                "minTtl": cb["min_ttl"],
                "defaultTtl": cb["default_ttl"],
                "maxTtl": cb["max_ttl"]
            }),
            price_class=existing_distribution.price_class,
            restrictions=existing_distribution.restrictions,
            viewer_certificate={
                "acmCertificateArn": certificate_arn,
                "sslSupportMethod": "sni-only",
                "minimumProtocolVersion": "TLSv1.2_2019",
            },
            aliases=[my_domain_name],
            comment=existing_distribution.comment,
            default_root_object=existing_distribution.default_root_object,
            custom_error_responses=existing_distribution.custom_error_responses,
            logging_config=existing_distribution.logging_config,
            ordered_cache_behaviors=existing_distribution.ordered_cache_behaviors,
            web_acl_id=existing_distribution.web_acl_id,
            http_version=existing_distribution.http_version,
        )

    # Apply the function to update the distribution
    updated_distribution = pulumi.Output.all(
        distribution,
        certificate.arn).apply(lambda args: update_distribution(*args))

    # Extract the nameservers for manual update on Namecheap.
    pulumi.export("Route 53 nameservers", hosted_zone.name_servers)
    pulumi.export("Updated CloudFront domain", updated_distribution.domain_name)
