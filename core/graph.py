# Wires the Phase 1 single-path cycle as a LangGraph StateGraph:
# ingest pool state -> ingest signals -> predict risk -> decide -> execute (or skip).
from __future__ import annotations

from langgraph.graph import StateGraph

from adapters.drips_adapter import DripsClient
from adapters.signal_adapter import SignalProvider
from adapters.soroban_adapter import PoolStateProvider
from agents.decision_agent import decide
from agents.prediction_agent import predict_risk
from config.settings import Settings
from core.state import ExecutionResult, GraphState


def build_graph(
    pool_provider: PoolStateProvider,
    signal_provider: SignalProvider,
    drips_client: DripsClient,
    settings: Settings,
):
    def ingest_pool_node(state: GraphState) -> GraphState:
        path = state["path"]
        state["pool_history"] = {
            pool_id: pool_provider.get_pool_history(pool_id) for pool_id in path.pool_ids
        }
        return state

    def ingest_signal_node(state: GraphState) -> GraphState:
        path = state["path"]
        # Signals are keyed by each hop's destination asset (the asset demand flows into).
        state["signals"] = {asset: signal_provider.get_signal(asset) for asset in path.hops[1:]}
        return state

    def predict_node(state: GraphState) -> GraphState:
        return predict_risk(state)

    def decide_node(state: GraphState) -> GraphState:
        return decide(state, settings)

    def execute_node(state: GraphState) -> GraphState:
        decision = state["decision"]
        state["execution_result"] = drips_client.adjust_stream(
            decision.target_pool_id, decision.proposed_delta
        )
        return state

    def skip_node(state: GraphState) -> GraphState:
        state["execution_result"] = ExecutionResult(
            success=True,
            detail="no action taken: below risk threshold, low confidence, or kill switch engaged",
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
    graph.add_node("execute", execute_node)
    graph.add_node("skip", skip_node)

    graph.set_entry_point("ingest_pool")
    graph.add_edge("ingest_pool", "ingest_signal")
    graph.add_edge("ingest_signal", "predict")
    graph.add_edge("predict", "decide")
    graph.add_conditional_edges(
        "decide", route_after_decision, {"execute": "execute", "skip": "skip"}
    )
    graph.set_finish_point("execute")
    graph.set_finish_point("skip")

    return graph.compile()
