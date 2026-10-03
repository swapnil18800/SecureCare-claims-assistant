"""Run a compiled graph and capture a node-by-node trace (for the UI) in a single pass."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

from securecare.graph.state import ClaimState
from securecare.logs import get_logger

log = get_logger("graph")


@dataclass
class RunResult:
    state: Dict[str, Any]
    trace: List[Dict[str, Any]] = field(default_factory=list)


def run_claim(graph, initial_state: ClaimState) -> RunResult:
    final_state: Dict[str, Any] = {}
    trace: List[Dict[str, Any]] = []
    started = time.perf_counter()
    log.info("workflow started (use_llm=%s)", initial_state.get("use_llm"))
    for mode, chunk in graph.stream(initial_state, stream_mode=["updates", "values"]):
        if mode == "updates":
            for node_name, update in chunk.items():
                trace.append({"step": len(trace) + 1, "node": node_name,
                              "updated": sorted((update or {}).keys())})
                for line in (update or {}).get("audit_log", []):     # audit lines hold no personal data
                    log.info("step %d %s | %s", len(trace), node_name, line)
        else:  # "values": full state after each step; the last one is the final state
            final_state = chunk
    log.info("workflow finished in %.1fs: claim=%s status=%s letters=%s",
             time.perf_counter() - started, final_state.get("claim_id"),
             final_state.get("status"), final_state.get("comms_source"))
    return RunResult(state=final_state, trace=trace)
