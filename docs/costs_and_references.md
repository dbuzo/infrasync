# InfraSync — References & Further Reading

This document collects references, run instructions, and links related to the work completed in this repository. It is intended as a single place for reviewers and maintainers to find:

- design references and architecture diagrams
- post-interview changes and rationale
- run & test commands
- cost and operational considerations
- external resources and vendor pricing links

Use this as the central reference when evaluating InfraSync for production use or for preparing follow-up discussions.

## Post-interview improvements (summary)

These items were added or improved after the interview exercise to harden the design and implementation:

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
- AWS Pricing: https://aws.amazon.com/pricing/
- AWS S3 Pricing: https://aws.amazon.com/s3/pricing/
- AWS DynamoDB Pricing: https://aws.amazon.com/dynamodb/pricing/
- Google Cloud Pricing: https://cloud.google.com/pricing
- Azure Pricing: https://azure.microsoft.com/pricing/
- GitHub Actions usage & pricing: https://docs.github.com/actions/learn-github-actions/usage-limits-billing-and-administration
- HashiCorp Remote State / HCP: https://www.hashicorp.com/products/terraform/cloud
- Monitoring: CloudWatch (https://aws.amazon.com/cloudwatch/pricing/), Datadog (https://www.datadoghq.com/pricing/)

## Contribution & contact

If you'd like to discuss the architecture, open an issue or contact the maintainer listed in the repository. For follow-up interviews or detailed walkthroughs, the `README.md` and `docs/mermaid_diagrams.md` contain the core talking points and visuals.

---

This references file is meant to be a living document — please suggest additions for any services, pricing links, or operational runbooks you want included.
