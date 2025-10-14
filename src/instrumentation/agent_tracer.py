from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .tracer import Tracer


class AgentTracer(Tracer):
    """
    Lightweight, test-friendly AgentTracer that extends the local Tracer and
    provides simple in-memory recording helpers for agent activities.

    This class is intentionally dependency-free and aligns with unit test
    expectations:
      - AgentTracer() constructs with no args
      - isinstance(AgentTracer(), Tracer) is True
      - Exposes _agent_spans dict
      - Methods:
          trace_agent_decision(...)
          trace_agent_action(...)
          trace_agent_learning(...)
          get_agent_trace(agent_id, trace_id)
          get_agent_traces(agent_id)
    """

    def __init__(self) -> None:
        super().__init__()
        self._agent_spans: Dict[str, Dict[str, Any]] = {}

    def trace_agent_decision(
        self,
        agent_id: str,
        decision_type: str,
        decision_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        trace_id = self.start_span("agent_decision")
        self._agent_spans[trace_id] = {
            "agent_id": agent_id,
            "decision_type": decision_type,
            "action_type": None,
            "decision_data": dict(decision_data) if decision_data else {},
            "context": dict(context) if context else {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "span_id": trace_id,
        }
        self.end_span(trace_id)
        return trace_id

    def trace_agent_action(
        self,
        agent_id: str,
        action_type: str,
        action_data: Dict[str, Any],
        result: Optional[Dict[str, Any]] = None,
    ) -> str:
        trace_id = self.start_span("agent_action")
        self._agent_spans[trace_id] = {
            "agent_id": agent_id,
            "action_type": action_type,
            "decision_type": None,
            "action_data": dict(action_data) if action_data else {},
            "result": dict(result) if result else {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "span_id": trace_id,
        }
        self.end_span(trace_id)
        return trace_id

    def trace_agent_learning(
        self,
        agent_id: str,
        learning_type: str,
        learning_data: Dict[str, Any],
        model_update: Optional[Dict[str, Any]] = None,
    ) -> str:
        trace_id = self.start_span("agent_learning")
        self._agent_spans[trace_id] = {
            "agent_id": agent_id,
            "learning_type": learning_type,
            "decision_type": None,
            "action_type": None,
            "learning_data": dict(learning_data) if learning_data else {},
            "model_update": dict(model_update) if model_update else {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "span_id": trace_id,
        }
        self.end_span(trace_id)
        return trace_id

    def get_agent_trace(self, agent_id: str, trace_id: str) -> Optional[Dict[str, Any]]:
        data = self._agent_spans.get(trace_id)
        if data and data.get("agent_id") == agent_id:
            return data
        return None

    def get_agent_traces(self, agent_id: str) -> List[Dict[str, Any]]:
        return [d for d in self._agent_spans.values() if d.get("agent_id") == agent_id]
