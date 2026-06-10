# InfraSync — References & Further Reading

This document collects references, run instructions, and links related to the work completed in this repository. It is intended as a single place for reviewers and maintainers to find:

- design references and architecture diagrams
- implementation changes and rationale
- run & test commands
- cost and operational considerations
- external resources and vendor pricing links

Use this as the central reference when evaluating InfraSync for production use or for preparing follow-up discussions.

## Recent improvements (summary)

These items were added or improved to harden the design and implementation:

- Adoption edge case: when desired config and real world match but the local state file is missing, InfraSync will now adopt the existing resource into state instead of attempting to recreate it. See `infrasync/plan.py` and `infrasync/engine.py`.
- Persisted dependency metadata: `ResourceState` now stores `depends_on` so destroy ordering can be computed from state. See `infrasync/models.py` and `infrasync/state.py`.
- Safer destroy ordering: `topological_sort()` gained an option to ignore missing dependencies; destroy now computes reverse-order using persisted dependency metadata. See `infrasync/graph.py` and `infrasync/engine.py`.
- Documentation: README updates describing adoption behavior, provider abstraction, and a new references doc (this file). Main architecture diagram restored at `docs/diagrams/system-architecture.png` and shown in `README.md`.

Commits: `1c1a9ac` (adoption & dependency changes), `0d880c4` (temporary cleanup), `1c039d2` (restored diagram), `846af3b` (added this references doc).

## Architecture & Design references

- Core design: three-way reconciliation (config vs state vs world) — see `README.md` and `docs/mermaid_diagrams.md`.
- Provider abstraction: implement the `Provider` interface in `infrasync/providers/base.py` and register types in `infrasync/providers/registry.py`.
- Dependency graph and ordering: `infrasync/graph.py` implements Kahn's algorithm for topological sorting; used by `plan` and `apply` flows.
- State model: `infrasync/state.py` and `infrasync/models.py` document how state is stored and versioned.

## Core concepts

These notes describe the core infrastructure concepts reflected in the implementation and recommended reference material.

- Desired state
  - The configuration that declares what resources should exist.
  - InfraSync uses the config as the source of truth for intended infrastructure.
- Actual state
  - The state last known to the tool, stored in `infrasync.state.json`.
  - It records resource metadata, fingerprints, and dependency relationships from the previous successful apply.
- Live state
  - The real-world state observed from the provider at runtime.
  - InfraSync compares live state to desired and actual state to detect drift and adoption opportunities.
- Drift detection and adoption
  - When live state differs from desired state, the engine treats that as drift and plans an update.
  - When live state matches desired state but actual state is missing or stale, the engine adopts the resource instead of recreating it.
- Remote state vs local missing files
  - Remote state files and provider-managed resources can be out of sync with local metadata.
  - InfraSync’s design supports recovering from missing local state by reconciling desired state with live provider state.
- AWS and cloud provider concepts
  - AWS resource management often relies on IAM, S3, DynamoDB, CloudWatch, and remote state locking.
  - The same reconciliation patterns apply whether the provider is a filesystem, cloud API, or custom backend.
- Security and SRE
  - Security documentation should cover access controls, secrets handling, auditability, and drift remediation.
  - SRE practices include observability, incident response, rollback planning, and safe destroy ordering.
- Subsystem management
  - Treat individual provider domains as subsystems with clear ownership, dependencies, and lifecycle rules.
  - This helps maintain stable applies and safe teardown ordering across resource types.

## How to run locally (quick commands)

1. Create a virtualenv and install deps:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Initialize state and run an example:

```bash
python -m infrasync init
python -m infrasync plan
python -m infrasync apply
```

3. Simulate drift and plan again:

```bash
echo "rogue edit" > ./managed/README.md
python -m infrasync plan
```

## Tests and validation

There are no automated tests included yet. Suggested minimal tests:

- Unit tests for `compute_plan()` scenarios: new resource, drift, config update, orphaned destroy.
- Integration tests for `FilesystemProvider` using a temporary directory.
- CI: add a lightweight GitHub Actions workflow to run unit tests and flake checks.

## Costs & operational considerations

See the Cost categories and best practices below (short summary):

- Resource costs depend on the provider — local filesystem has no cloud cost.
- Remote state backends (S3/GCS/Azure) add storage and egress charges.
- Locking (DynamoDB or similar) enables safe concurrent applies at a small cost.
- Monitoring, logging, CI runners, and network egress are additional operational expenses.

For detailed links and price pages, see the external references section below.

## External references & pricing links

- Terraform docs: https://www.terraform.io/docs
- Terraform state & remote backend: https://www.terraform.io/language/state
- Terraform provider development: https://www.terraform.io/plugin/sdk
- AWS Pricing: https://aws.amazon.com/pricing/
- AWS S3 Pricing: https://aws.amazon.com/s3/pricing/
- AWS DynamoDB Pricing: https://aws.amazon.com/dynamodb/pricing/
- AWS IAM best practices: https://aws.amazon.com/iam/
- AWS CloudWatch pricing: https://aws.amazon.com/cloudwatch/pricing/
- AWS CloudFormation docs: https://docs.aws.amazon.com/cloudformation/index.html
- AWS Well-Architected Framework: https://aws.amazon.com/architecture/well-architected/
- Google Cloud Pricing: https://cloud.google.com/pricing
- Azure Pricing: https://azure.microsoft.com/pricing/
- GitHub Actions usage & pricing: https://docs.github.com/actions/learn-github-actions/usage-limits-billing-and-administration
- HashiCorp Remote State / HCP: https://www.hashicorp.com/products/terraform/cloud
- Remote state and drift detection: https://www.terraform.io/language/state/sensitive-data
- Security best practices: https://owasp.org/www-project-top-ten/
- Secrets management: https://www.vaultproject.io/docs
- SRE guidance: https://sre.google/sre-book/table-of-contents/
- Observability and incident response: https://landing.google.com/sre/workbook/
- Monitoring and logging: CloudWatch (https://aws.amazon.com/cloudwatch/pricing/), Datadog (https://www.datadoghq.com/pricing/)

## Contribution & contact

If you'd like to discuss the architecture, open an issue or contact the maintainer listed in the repository. For detailed walkthroughs, the `README.md` and `docs/mermaid_diagrams.md` contain the core talking points and visuals.

---

This references file is meant to be a living document — please suggest additions for any services, pricing links, or operational runbooks you want included.
