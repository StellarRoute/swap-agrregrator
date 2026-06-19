# Product Requirements Document: StellarHydra — Agentic Liquidity Balancer (ALB)

## 1. Problem Statement

Stellar's path-payment routing engine (StellarRoute) computes the "best" swap path using **only the current, static on-chain order book and AMM pool state**. This is reactive by construction: it tells a trader what the optimal route is *right now*, but it has no mechanism to anticipate that a route is about to degrade.

In practice, liquidity on any given multi-hop path (e.g. `XLM -> USDC -> Minor Asset`) is thin and volatile. A burst of trading volume, a sentiment-driven flight to a particular asset, or a large single order can deplete a pool's depth in seconds, causing:

- **Slippage spikes** for traders who get routed into a pool moments before it gets drained.
- **Route flapping**, where the "optimal" path changes rapidly block-to-block, producing inconsistent quotes.
- **Idle capital** for liquidity providers (LPs), whose funds sit in pools that are not currently on the optimal route, earning little, while the pools that *are* on the optimal route are under-capitalized relative to demand.

The core pain: **liquidity is statically allocated while demand is dynamic**, and no agent in the current stack acts *ahead* of demand to keep the route StellarRoute is about to recommend already well-funded.

## 2. Target Users

| User | Context | What they need from StellarHydra |
|---|---|---|
| **Liquidity Providers (LPs)** | Provide capital to Stellar DEX / Soroban AMM pools, currently rebalance manually or via simple static rules | Capital that is proactively redeployed to pools about to see demand, improving yield and reducing idle/at-risk exposure |
| **Traders / Swap Aggregator users** | Query StellarRoute (or a downstream swap aggregator UI) for the best price on a multi-hop swap | Routes that are stable and well-funded at execution time, not just at quote time — lower realized slippage |
| **Protocol / Pool Operators (StellarRoute team)** | Operate the routing engine and want to reduce user-visible slippage and route instability | A system that improves realized execution quality without requiring changes to the core routing contract logic |
| **Quant/Ops Engineer (internal)** | Configures, monitors, and tunes the prediction and rebalancing agents | Observability into agent decisions, the ability to set risk limits, and a kill switch |

These users do not directly operate LangGraph or Soroban contracts themselves (except the Quant/Ops Engineer) — StellarHydra runs as an autonomous backend service that acts on their behalf within configured limits.

## 3. Goals and Non-Goals

### Goals

- Predict, ahead of time, which Stellar DEX multi-hop paths are at risk of high slippage or liquidity bottlenecks, using external signals (market velocity, sentiment, historical pool transaction patterns) in addition to on-chain state.
- Translate those predictions into concrete liquidity rebalancing actions, expressed as adjustments to a Drips continuous funding stream, so capital proactively migrates toward at-risk paths *before* the bottleneck materializes.
- Keep all rebalancing actions auditable, bounded by configurable risk limits, and reversible.
- Demonstrate, end-to-end in a simulated/testnet environment, that a predicted bottleneck results in a stream adjustment that increases liquidity depth on the targeted path ahead of the predicted demand window.

### Non-Goals

- StellarHydra does **not** replace or modify StellarRoute's core path-finding algorithm. It is a complementary system that influences the *liquidity available to* that algorithm, not the algorithm itself.
- StellarHydra does **not** execute trades on behalf of users or act as a market maker taking principal risk. It only manages LP-supplied capital that has been explicitly delegated to it via Drips streams.
- StellarHydra does **not** provide a trading UI or wallet. It is a backend agentic service; any user-facing surface is out of scope for this PRD.
- No mainnet fund custody in the initial build — V1 targets Stellar **testnet** with simulated or testnet Drips streams only.
- No multi-chain support. Stellar/Soroban only.
- No general-purpose sentiment/NLP model training — V1 consumes existing third-party sentiment/market-data APIs rather than building new ones.

## 4. Core Features

| # | Feature | Description | Acceptance Criterion |
|---|---|---|---|
| F1 | **On-chain Pool State Ingestion** | Periodically pull current Stellar DEX / Soroban AMM pool reserves, recent swap volume, and StellarRoute's currently-quoted paths. | Given a configured set of assets, the system stores a time-series snapshot of pool reserves and volume at a configurable polling interval (default 30s), with no gaps longer than 2x the interval under normal operation. |
| F2 | **External Signal Ingestion** | Pull market velocity (price/volume momentum) and sentiment index data for tracked assets from configured external APIs. | Given a tracked asset, the system produces a normalized signal record (velocity score, sentiment score, timestamp) at least once per polling cycle, and gracefully degrades (flagging the signal as stale) if the upstream API fails. |
| F3 | **Bottleneck Prediction Agent** | A LangGraph agent node that combines on-chain history (F1) with external signals (F2) to score each tracked multi-hop path for predicted slippage/bottleneck risk over a forward time window. | Given historical pool + signal data for a path, the agent emits a risk score (0–1) and a confidence value for that path, and this output is reproducible (same inputs -> same score) and logged with the inputs that produced it. |
| F4 | **Rebalancing Decision Agent** | A LangGraph agent node that, given path risk scores from F3, decides whether and how much to adjust Drips liquidity streams toward at-risk paths' pools, subject to configured risk limits (max stream delta, max % of pool capital, cooldown period). | Given a path risk score above the configured threshold, the agent proposes a stream adjustment that never exceeds the configured max delta/cooldown, and proposes no action when all scores are below threshold. |
| F5 | **Drips Stream Adjustment Executor** | Executes approved rebalancing decisions by calling the Drips API to modify a continuous funding stream's split/amount toward the target pool's liquidity-provisioning address. | Given an approved decision, the executor submits a Drips API call and records success/failure; on failure it retries with backoff up to a configured limit and surfaces the final state. |
| F6 | **Soroban Contract Interface** | A typed interface layer that reads StellarRoute's Soroban contract state (pool reserves, route quotes) needed by F1, isolated behind an adapter so the rest of the system is not coupled to contract ABI details. | Given a deployed/testnet StellarRoute contract address, the adapter returns parsed pool reserve and quote data matching the contract's actual on-chain values, verified against a direct RPC query. |
| F7 | **Agent Orchestration Loop (LangGraph)** | A stateful graph wiring F1→F3, F2→F3, F3→F4, F4→F5 as a recurring decision loop, with persisted state between runs. | Given the loop is running, one full cycle (ingest → predict → decide → execute-or-skip) completes and is logged with a unique run ID, and the loop resumes correctly after a process restart using persisted state. |
| F8 | **Risk Limits & Kill Switch** | Configurable hard limits (max capital moved per cycle, per-path cap, global pause) enforced centrally, independent of agent logic. | Given a kill switch is engaged, no further Drips executor calls are made until it is disengaged, regardless of agent output. |
| F9 | **Observability & Audit Log** | Structured logs/metrics for every prediction, decision, and execution, queryable by path, time range, and run ID. | Given any executed rebalancing action, an operator can trace it back to the specific risk scores and signal inputs that triggered it. |
| F10 | **Task Queue for Long-Running Work** | Redis/Celery-style worker queue to decouple ingestion, prediction, and execution from the orchestration loop's tick rate, so slow external calls don't block the loop. | Given an external API call (sentiment, Drips, RPC) is slow or hung, the orchestration loop's next tick is not blocked beyond a configured timeout. |

## 5. Technical Constraints

- **Language/runtime:** Python 3.11+ for the agentic backend (LangGraph, Celery workers, ingestion). Rust is read-only context here — StellarRoute's Soroban contracts are an existing external dependency, not something this project builds or modifies.
- **Agent framework:** LangGraph for all stateful multi-agent orchestration (prediction, decision, execution as graph nodes with persisted checkpoints).
- **Task queue:** Celery with Redis as broker/backend for ingestion and execution workers.
- **On-chain access:** Soroban RPC (via `stellar-sdk` / soroban RPC HTTP endpoint) to read StellarRoute contract state. Testnet only for V1.
- **Liquidity streaming:** Drips Wave API for programmable continuous cash-flow streams; integration via Drips' REST/GraphQL API and GitHub-linked accounts as per Drips Wave conventions.
- **External data:** Pluggable provider interfaces for market velocity and sentiment data (concrete provider TBD — see Open Questions).
- **Persistence:** Postgres (or SQLite for local dev) for time-series snapshots, agent run history, and audit logs; Redis for queue + ephemeral state/cache.
- **Environment assumptions:** Service runs as a long-lived backend process (not serverless) since LangGraph loop + Celery workers expect persistent connections. Deployable as containerized services (API/orchestrator, worker, Redis, Postgres).
- **Secrets:** Drips API keys, Soroban signing keys, and external API keys are supplied via environment variables / secrets manager — never committed to source.
- **No mainnet fund movement in V1** — all Drips stream adjustments and Soroban interactions target testnet.

## 6. Open Questions

1. **Drips integration shape:** Does Drips Wave support testnet-equivalent streams today, or does V1 need a mock/simulated Drips adapter until a sandbox is available?
2. **Sentiment/market-velocity data source:** Which concrete provider(s) (e.g., a specific market data API, a specific sentiment index) are licensed/approved for use? This determines the shape of the F2 adapter.
3. **StellarRoute contract interface:** Is there an existing StellarRoute Soroban contract ABI/SDK to integrate against, or does F6 need to be built from raw RPC calls against an assumed contract layout?
4. **Capital delegation model:** How does an LP actually delegate a Drips stream to StellarHydra's control — is there an existing authorization/delegation mechanism, or does this need to be designed as part of this project?
5. **Risk limit defaults:** What are acceptable default values for max capital moved per cycle / per-path caps, pending input from whoever owns LP risk policy?
6. **Prediction model approach:** Is a rules/heuristics-based scoring model (combining velocity + sentiment + historical variance) sufficient for V1, or is a trained ML model expected from the start? This PRD assumes heuristic scoring for V1 with room to swap in a trained model later.
7. **Path universe:** Is the initial tracked path set fixed/curated (e.g., a short list of known major routes) or should it be auto-discovered from StellarRoute's quoting activity?
