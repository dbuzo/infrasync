# InfraSync — Costs, Pricing & References

This page summarizes cost considerations, pricing references, and links for teams evaluating or running InfraSync in production. Use this as a starting point for budget planning and vendor research.

## Overview

InfraSync itself is a small Python tool; direct costs come from the resources it manages and the infrastructure used to store state, locking, CI, and monitoring. Review the sections below to understand where charges may occur.

## Cost Categories

- Resource costs: Any cloud or SaaS resources managed by providers (VMs, databases, storage buckets).
- State storage: Remote state backends (S3, GCS, Azure Blob) incur storage and egress costs.
- Locking and coordination: DynamoDB/Cloud Datastore or managed lock services may have per-request and storage costs.
- API calls / rate limits: Providers like AWS, GitHub, or third-party APIs may charge for calls or impose rate limits that affect throughput.
- CI / automation: GitHub Actions, GitLab CI, or other runners may incur compute minutes or concurrency costs.
- Monitoring & logging: CloudWatch, Stackdriver, Datadog, etc., add storage and ingest costs for logs and metrics.
- Network egress: Cross-region or public internet egress for backups, state sync, or provider API traffic.

## Examples & Ballpark Estimates

- Local filesystem provider: effectively zero cloud costs (local disk I/O only).
- Remote state in S3 + DynamoDB locking (small team, light usage): expect low cents-per-month for state objects; DynamoDB on-demand requests may add a few dollars monthly depending on frequency. See AWS pricing below for details.
- Managing an EC2 or Cloud VM: assume base VM pricing + storage (EBS) + network. See AWS EC2/EBS pricing.

Note: Actual costs vary widely by region, instance types, retention policies, and usage patterns. Use provider calculators for precise budgeting.

## Best Practices to Reduce Costs

- Use local providers for development and testing to avoid cloud fees.
- Retain minimal state history and compress/expire old logs to reduce storage costs.
- Batch operations where possible to reduce API call volume.
- Use reserved or saving-plan options for predictable long-running resources.
- Add quotas and alerts to detect runaway automation that increases bill unexpectedly.

## Operational Considerations

- State backups: store encrypted backups of state (S3 lifecycle rules) and account for storage and retrieval costs.
- Concurrency: if multiple CI runners may run `apply` concurrently, implement remote locking to avoid race conditions—this can add small additional costs.
- Import vs adopt: importing existing resources may require extra API calls and verification steps.

## References and Pricing Links

- Terraform docs: https://www.terraform.io/docs
- AWS Pricing: https://aws.amazon.com/pricing/
- AWS S3 Pricing: https://aws.amazon.com/s3/pricing/
- AWS DynamoDB Pricing: https://aws.amazon.com/dynamodb/pricing/
- Google Cloud Pricing: https://cloud.google.com/pricing
- Azure Pricing: https://azure.microsoft.com/pricing/
- GitHub Actions usage & pricing: https://docs.github.com/actions/learn-github-actions/usage-limits-billing-and-administration
- HashiCorp Remote State / HCP: https://www.hashicorp.com/products/terraform/cloud
- Monitoring: CloudWatch (https://aws.amazon.com/cloudwatch/pricing/), Datadog (https://www.datadoghq.com/pricing/)

## Template checklist for estimating costs

1. List resources to manage (type, count, region).
2. Identify state backend and locking mechanism.
3. Estimate frequency of `plan`/`apply` runs and API call volume.
4. Add storage and monitoring retention estimates.
5. Run provider cost calculators and add a monthly buffer (e.g., 20%).

## Notes

This document is a starting point. For production deployments, create a dedicated runbook or cost model that lists concrete resource types, sizes, and retention policies.