# Roadmap: StellarHydra — Agentic Liquidity Balancer (ALB)

Derived from [PRD.md](./PRD.md). Open questions (Drips testnet shape, sentiment provider, StellarRoute SDK, capital delegation model) are unresolved at the protocol/business level — this roadmap unblocks engineering by building against **mock/simulated adapters** for those integrations, with real adapters swapped in behind the same interface once those questions are answered.

---

## Phase 0: Scaffold

| | |
|---|---|
| **Objective** | Stand up the project skeleton — structure, config, dependency manifest, and CI — so every later phase has a consistent place to land code. |

| Deliverables |
|---|
| Repo folder structure (`agents/`, `adapters/`, `workers/`, `core/`, `tests/`, `config/`) |
| `pyproject.toml` / `requirements.txt` with pinned core deps (langgraph, celery, redis, sqlalchemy, stellar-sdk, httpx, pydantic) |
| `.env.example` documenting all required environment variables |
| `config/settings.py` — typed settings loader (pydantic-settings) |
| Dockerfile + `docker-compose.yml` (app, worker, redis, postgres) for local dev |
| CI skeleton (`.github/workflows/ci.yml`) running lint + unit tests on push |
| `README.md` with setup instructions |
| Logging configuration (structured JSON logs) |

| Exit Criteria |
|---|
| `docker-compose up` brings up app + worker + redis + postgres containers without crash-looping |
| `pytest` runs (even with zero/placeholder tests) and CI workflow is syntactically valid |
| Settings object loads from `.env` and fails fast with a clear error if a required var is missing |

**Estimated complexity:** Low

---

## Phase 1: Core Loop

| | |
|---|---|
| **Objective** | Prove the end-to-end concept: ingest pool state → score one path's bottleneck risk → decide → execute a (mocked) Drips stream adjustment, as a single LangGraph run. |

| Deliverables |
|---|
| `adapters/soroban_adapter.py` — reads pool reserves for a configured path (real RPC call against testnet, or fixture-backed if no contract address is available yet) |
| `adapters/signal_adapter.py` — mock/stub external velocity + sentiment signal provider behind a real interface (`SignalProvider` ABC) |
| `agents/prediction_agent.py` — heuristic risk scoring node (combines pool reserve trend + signal data into a 0–1 risk score + confidence) |
| `agents/decision_agent.py` — thresholds risk score against configured limits, emits a `RebalanceDecision` (act / no-act) |
| `adapters/drips_adapter.py` — `MockDripsClient` implementing the real `DripsClient` interface, logging stream-adjustment calls instead of hitting the network |
| `core/graph.py` — LangGraph `StateGraph` wiring ingestion → prediction → decision → execution for **one path** |
| `core/state.py` — typed graph state (pydantic model) |
| `scripts/run_once.py` — CLI entrypoint to run a single end-to-end cycle and print the trace |
| Unit tests for prediction scoring math and decision thresholding |

| Exit Criteria |
|---|
| Running `scripts/run_once.py` against a configured path produces a logged trace: pool snapshot → signal snapshot → risk score → decision → (mock) executor call or explicit no-action |
| Changing input fixtures (e.g. simulating a volume spike) measurably changes the risk score and resulting decision — proving the prediction → action link works |
| All Phase 1 components are swappable (real adapter can replace mock without touching agent code), validated by at least one test using a fake adapter |

**Estimated complexity:** Medium

---

## Phase 2: Feature Complete

| | |
|---|---|
| **Objective** | Extend the proven core loop to all PRD features — multi-path tracking, persistence, the task queue, risk limits/kill switch, and observability — with real edge-case and error handling. |

| Deliverables |
|---|
| `core/orchestrator.py` — recurring loop (not single-shot) managing multiple tracked paths concurrently, with LangGraph checkpointing to Postgres for resume-after-restart |
| `workers/celery_app.py` + `workers/tasks.py` — Celery tasks for ingestion, signal polling, and executor calls, decoupled from the orchestration tick |
| `db/models.py` + migrations — pool snapshots, signal snapshots, agent run history, audit log tables |
| `core/risk_limits.py` — centralized enforcement of max-delta, per-path cap, cooldown, and a global kill switch flag (checked independently of agent output) |
| `core/observability.py` — structured logging + metrics (counts, latencies, last-N decisions) queryable by path/time/run ID |
| Error-state handling: stale/failed signal source (F2), Soroban RPC timeout (F1/F6), Drips executor failure with retry/backoff (F5) |
| `adapters/signal_adapter.py` real provider implementation (or clearly-flagged mock if Open Question #2 still unresolved) |
| Expanded test suite: multi-path runs, kill-switch engagement, retry/backoff behavior, restart-resume correctness |

| Exit Criteria |
|---|
| Orchestrator runs continuously across multiple configured paths, persisting state such that a process kill + restart resumes without duplicate or lost executor calls |
| Kill switch, when engaged, provably blocks all executor calls even when decision agent outputs "act" |
| Simulated upstream failures (signal API down, RPC timeout, Drips API error) are handled per F2/F5 acceptance criteria — no unhandled exceptions crash the loop |
| An operator can trace any executed action back to its triggering risk score and inputs via the audit log (F9) |

**Estimated complexity:** High

---

## Phase 3: Production Hardening

| | |
|---|---|
| **Objective** | Make the system safe, observable, and deployable against real (testnet) infrastructure with real Drips streams, not just mocks. |

| Deliverables |
|---|
| Real `DripsClient` implementation against the Drips Wave API (auth via API key/secrets manager), replacing `MockDripsClient` |
| Secrets management wiring (env vars sourced from a secrets manager in deployed environments; never committed) |
| AuthN/authZ on any operator-facing surface (e.g. admin endpoint to view audit log / trigger kill switch) — minimal API-key or token gate |
| Metrics/alerting integration (Prometheus-style metrics export; alert on kill-switch engagement, repeated executor failures, stale signal sources) |
| Performance pass: polling interval tuning, Celery concurrency/queue sizing, DB indices on time-series tables for the access patterns observability needs |
| Deployment pipeline: container images built and pushed in CI, deploy manifests (docker-compose for staging at minimum; k8s manifests if target infra requires it) |
| Runbook documentation: how to engage kill switch, how to rotate a misbehaving signal provider, how to read the audit log for an incident |
| Load/chaos test: simulate sustained signal-provider outage and Drips API outage; verify system degrades to "no-action, logged" rather than failing unsafely |

| Exit Criteria |
|---|
| End-to-end run against real testnet Soroban contract + real Drips Wave testnet/sandbox stream succeeds and is auditable |
| All secrets are sourced from environment/secrets manager with none present in source control (verified by secret-scanning in CI) |
| CI pipeline builds, tests, and deploys to a staging environment on merge to main |
| Documented runbook exists and the kill switch has been exercised in a staging drill |

**Estimated complexity:** High

---

## Summary Timeline

| Phase | Objective | Complexity | Primary Risk |
|---|---|---|---|
| 0 — Scaffold | Project skeleton, config, CI | Low | None significant |
| 1 — Core Loop | One path, mocked adapters, proves prediction→action link | Medium | Heuristic scoring may need iteration once real signal data shape is known |
| 2 — Feature Complete | Multi-path, persistence, queue, risk limits, error handling | High | Restart/resume correctness and concurrent multi-path state are the hardest parts |
| 3 — Production Hardening | Real Drips integration, auth, observability, deploy | High | Blocked on Open Questions #1–#4 (Drips testnet shape, capital delegation model) until resolved with stakeholders |
