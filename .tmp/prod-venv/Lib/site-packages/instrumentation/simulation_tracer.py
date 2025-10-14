from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .tracer import Tracer


class SimulationTracer(Tracer):
    """
    Lightweight, dependency-free SimulationTracer extending the local Tracer.

    Matches unit test expectations:
      - SimulationTracer() constructs with no args
      - isinstance(SimulationTracer(), Tracer) is True
      - Exposes _simulation_spans dict
      - Methods:
          trace_simulation_event(event_type, event_data, tick, scenario_id)
          trace_simulation_state(state_data, tick, scenario_id)
          trace_simulation_metrics(metrics_data, tick, scenario_id)
          get_simulation_trace(scenario_id, trace_id)
          get_simulation_traces_by_tick(scenario_id, tick)
          get_simulation_traces_by_scenario(scenario_id)
    """

    def __init__(self) -> None:
        super().__init__()
        self._simulation_spans: Dict[str, Dict[str, Any]] = {}

    def trace_simulation_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        tick: int,
        scenario_id: str,
    ) -> str:
        trace_id = self.start_span("simulation_event")
        self._simulation_spans[trace_id] = {
            "event_type": event_type,
            "event_data": dict(event_data) if event_data else {},
            "tick": int(tick),
            "scenario_id": scenario_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "span_id": trace_id,
        }
        self.end_span(trace_id)
        return trace_id

    def trace_simulation_state(
        self,
        state_data: Dict[str, Any],
        tick: int,
        scenario_id: str,
    ) -> str:
        trace_id = self.start_span("simulation_state")
        self._simulation_spans[trace_id] = {
            "state_data": dict(state_data) if state_data else {},
            "tick": int(tick),
            "scenario_id": scenario_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "span_id": trace_id,
        }
        self.end_span(trace_id)
        return trace_id

    def trace_simulation_metrics(
        self,
        metrics_data: Dict[str, Any],
        tick: int,
        scenario_id: str,
    ) -> str:
        trace_id = self.start_span("simulation_metrics")
        self._simulation_spans[trace_id] = {
            "metrics_data": dict(metrics_data) if metrics_data else {},
            "tick": int(tick),
            "scenario_id": scenario_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "span_id": trace_id,
        }
        self.end_span(trace_id)
        return trace_id

    def get_simulation_trace(self, scenario_id: str, trace_id: str) -> Optional[Dict[str, Any]]:
        data = self._simulation_spans.get(trace_id)
        if data and data.get("scenario_id") == scenario_id:
            return data
        return None

    def get_simulation_traces_by_tick(self, scenario_id: str, tick: int) -> List[Dict[str, Any]]:
        t = int(tick)
        return [
            d
            for d in self._simulation_spans.values()
            if d.get("scenario_id") == scenario_id and d.get("tick") == t
        ]

    def get_simulation_traces_by_scenario(self, scenario_id: str) -> List[Dict[str, Any]]:
        return [d for d in self._simulation_spans.values() if d.get("scenario_id") == scenario_id]
