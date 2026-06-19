# swap-agrregrator documentation

Also known as the StellarHydra ALB implementation in this repository.

## Product

| Doc | Description |
|-----|-------------|
| [../PRD.md](../PRD.md) | Product requirements |
| [../ROADMAP.md](../ROADMAP.md) | Phased build plan |
| [../RUNBOOK.md](../RUNBOOK.md) | Operator runbook |

## Architecture

| Doc | Description |
|-----|-------------|
| [architecture/overview.md](architecture/overview.md) | System components |
| [architecture/langgraph-pipeline.md](architecture/langgraph-pipeline.md) | Graph nodes |

## Development

| Doc | Description |
|-----|-------------|
| [development/SETUP.md](development/SETUP.md) | Local install |
| [development/testing.md](development/testing.md) | pytest guide |
| [configuration/env-vars.md](configuration/env-vars.md) | Environment reference |

## Components

| Doc | Description |
|-----|-------------|
| [agents/prediction-and-decision.md](agents/prediction-and-decision.md) | Agent logic |
| [adapters/drips-adapter.md](adapters/drips-adapter.md) | Drips client |
| [adapters/signal-adapter.md](adapters/signal-adapter.md) | Signal providers |
| [core/risk-limits.md](core/risk-limits.md) | Risk caps |
| [core/kill-switch.md](core/kill-switch.md) | Runtime kill switch |
| [workers/celery-tasks.md](workers/celery-tasks.md) | Background tasks |
| [database/models-and-migrations.md](database/models-and-migrations.md) | Postgres schema |

## Operations

| Doc | Description |
|-----|-------------|
| [api/admin-api.md](api/admin-api.md) | Admin endpoints |
| [observability/metrics-and-alerting.md](observability/metrics-and-alerting.md) | Metrics |
| [security/secrets-and-admin-auth.md](security/secrets-and-admin-auth.md) | API key auth |
| [deployment/kubernetes.md](deployment/kubernetes.md) | k8s manifests |
| [troubleshooting/common-issues.md](troubleshooting/common-issues.md) | FAQ |
