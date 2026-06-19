# Recurring, multi-path, queue-backed orchestration loop (PRD F7) with a pluggable LangGraph
# checkpointer for resume-after-restart, centrally-enforced risk limits (F8), and a
# per-path audit log entry (F9) written after every cycle. One path's failure is isolated
# from the rest so a single bad cycle can't take down the whole loop.
from __future__ import annotations

import time
import uuid

from celery.exceptions import TimeoutError as CeleryTimeoutError
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import StateGraph

from agents.decision_agent import decide
from agents.prediction_agent import predict_risk
from config.settings import Settings, get_settings
from core.alerting import alert_sink
from core.kill_switch import kill_switch
from core.observability import (
    configure_logging,
    decisions_total,
    executor_failures_total,
    get_logger,
    kill_switch_engaged_gauge,
    metrics,
    stale_signal_total,
)
from core.risk_limits import RiskLimitEnforcer
from core.state import ExecutionResult, GraphState, PathConfig, PoolSnapshot, SignalSnapshot
from db.models import AgentRunLog
from db.session import SessionFactory
from workers.tasks import execute_drips_adjustment_task, ingest_pool_task, ingest_signal_task

logger = get_logger(__name__)


def _build_queued_graph(
    settings: Settings, risk_limit_enforcer: RiskLimitEnforcer, checkpointer: BaseCheckpointSaver
):
    task_timeout = max(settings.pool_poll_interval_seconds, settings.signal_poll_interval_seconds, 10)
    consecutive_executor_failures: dict[str, int] = {}

    def ingest_pool_node(state: GraphState) -> GraphState:
        path = state["path"]
        history: dict[str, list[PoolSnapshot]] = {}
        for pool_id in path.pool_ids:
            try:
                raw = ingest_pool_task.delay(pool_id).get(timeout=task_timeout)
                history[pool_id] = [PoolSnapshot(**item) for item in raw]
            except CeleryTimeoutError:
                logger.warning("pool ingestion timed out for pool_id=%s; using empty history", pool_id)
                history[pool_id] = []
        state["pool_history"] = history
        return state

    def ingest_signal_node(state: GraphState) -> GraphState:
        path = state["path"]
        signals: dict[str, SignalSnapshot] = {}
        for asset in path.hops[1:]:
            try:
                raw = ingest_signal_task.delay(asset).get(timeout=task_timeout)
                signals[asset] = SignalSnapshot(**raw)
            except CeleryTimeoutError:
                logger.warning("signal ingestion timed out for asset=%s; marking stale", asset)
                signals[asset] = SignalSnapshot(
                    asset=asset, velocity_score=0.0, sentiment_score=0.0, stale=True
                )
            if signals[asset].stale:
                stale_signal_total.labels(asset=asset).inc()
                alert_sink.alert(
                    "stale signal source", f"asset={asset} signal is stale or failed to ingest"
                )
        state["signals"] = signals
        return state

    def predict_node(state: GraphState) -> GraphState:
        return predict_risk(state)

    def decide_node(state: GraphState) -> GraphState:
        return decide(state, settings)

    def enforce_limits_node(state: GraphState) -> GraphState:
        with SessionFactory() as session:
            state["decision"] = risk_limit_enforcer.authorize(state["decision"], session)
        return state

    def execute_node(state: GraphState) -> GraphState:
        decision = state["decision"]
        path_id = state["path"].path_id
        try:
            raw = execute_drips_adjustment_task.delay(
                decision.target_pool_id, decision.proposed_delta
            ).get(timeout=task_timeout)
            state["execution_result"] = ExecutionResult(**raw)
        except CeleryTimeoutError:
            state["execution_result"] = ExecutionResult(
                success=False, detail="drips executor task did not complete within timeout"
            )
        except Exception as exc:  # Drips failure surfaced by the task after its own retries (F5)
            state["execution_result"] = ExecutionResult(success=False, detail=str(exc))

        if state["execution_result"].success:
            consecutive_executor_failures[path_id] = 0
        else:
            executor_failures_total.inc()
            consecutive_executor_failures[path_id] = consecutive_executor_failures.get(path_id, 0) + 1
            if consecutive_executor_failures[path_id] >= settings.executor_failure_alert_threshold:
                alert_sink.alert(
                    "repeated executor failures",
                    f"path_id={path_id} failed {consecutive_executor_failures[path_id]} "
                    f"consecutive times: {state['execution_result'].detail}",
                    severity="critical",
                )
        return state

    def skip_node(state: GraphState) -> GraphState:
        state["execution_result"] = ExecutionResult(
            success=True, detail="no action taken: below threshold, low confidence, or blocked"
        )
        return state

    def route_after_decision(state: GraphState) -> str:
        decision = state["decision"]
        return "execute" if decision and decision.action == "act" else "skip"

    graph = StateGraph(GraphState)
    graph.add_node("ingest_pool", ingest_pool_node)
    graph.add_node("ingest_signal", ingest_signal_node)
    graph.add_node("predict", predict_node)
    graph.add_node("decide", decide_node)
    graph.add_node("enforce_limits", enforce_limits_node)
    graph.add_node("execute", execute_node)
    graph.add_node("skip", skip_node)

    graph.set_entry_point("ingest_pool")
    graph.add_edge("ingest_pool", "ingest_signal")
    graph.add_edge("ingest_signal", "predict")
    graph.add_edge("predict", "decide")
    graph.add_edge("decide", "enforce_limits")
    graph.add_conditional_edges(
        "enforce_limits", route_after_decision, {"execute": "execute", "skip": "skip"}
    )
    graph.set_finish_point("execute")
    graph.set_finish_point("skip")

    return graph.compile(checkpointer=checkpointer)


def _default_checkpointer(settings: Settings):
    from langgraph.checkpoint.postgres import PostgresSaver

    return PostgresSaver.from_conn_string(settings.database_url)


class Orchestrator:
    """Runs the queued multi-agent cycle for every tracked path, on a recurring tick."""

    def __init__(
        self,
        paths: list[PathConfig],
        settings: Settings | None = None,
        checkpointer: BaseCheckpointSaver | None = None,
    ) -> None:
        self._paths = paths
        self._settings = settings or get_settings()
        self._risk_limit_enforcer = RiskLimitEnforcer(self._settings)

        if checkpointer is not None:
            self._checkpointer = checkpointer
            self._checkpointer_cm = None
        else:
            self._checkpointer_cm = _default_checkpointer(self._settings)
            self._checkpointer = self._checkpointer_cm.__enter__()
            self._checkpointer.setup()

        self._graph = _build_queued_graph(
            self._settings, self._risk_limit_enforcer, self._checkpointer
        )

    def close(self) -> None:
        if self._checkpointer_cm is not None:
            self._checkpointer_cm.__exit__(None, None, None)

    def run_cycle(self) -> None:
        engaged = self._settings.kill_switch_engaged or kill_switch.engaged
        kill_switch_engaged_gauge.set(1 if engaged else 0)
        if engaged:
            alert_sink.alert("kill switch engaged", "no rebalancing actions will be executed")

        for path in self._paths:
            run_id = str(uuid.uuid4())
            try:
                final_state = self._graph.invoke(
                    {
                        "run_id": run_id,
                        "path": path,
                        "pool_history": {},
                        "signals": {},
                        "risk_assessment": None,
                        "decision": None,
                        "execution_result": None,
                    },
                    config={"configurable": {"thread_id": path.path_id}},
                )
                self._persist_run(final_state)
            except Exception:
                logger.exception("cycle failed for path_id=%s; continuing to next path", path.path_id)
                metrics.increment("orchestrator.cycle_failures")
                continue

    def _persist_run(self, state: GraphState) -> None:
        risk = state["risk_assessment"]
        decision = state["decision"]
        execution = state["execution_result"]
        with SessionFactory() as session:
            session.add(
                AgentRunLog(
                    run_id=state["run_id"],
                    path_id=state["path"].path_id,
                    risk_score=risk.risk_score,
                    confidence=risk.confidence,
                    risk_inputs=risk.inputs,
                    decision_action=decision.action,
                    decision_reason=decision.reason,
                    proposed_delta=decision.proposed_delta,
                    target_pool_id=decision.target_pool_id,
                    execution_success=execution.success,
                    execution_detail=execution.detail,
                )
            )
            session.commit()
        metrics.increment(f"orchestrator.decisions.{decision.action}")
        metrics.record_decision(state["path"].path_id, decision.action, risk.risk_score)
        decisions_total.labels(action=decision.action).inc()

    def run_forever(self, interval_seconds: int | None = None) -> None:
        interval = interval_seconds or self._settings.pool_poll_interval_seconds
        configure_logging(self._settings.log_level)
        logger.info(
            "orchestrator starting: %d tracked paths, interval=%ss", len(self._paths), interval
        )
        try:
            while True:
                self.run_cycle()
                time.sleep(interval)
        finally:
            self.close()
