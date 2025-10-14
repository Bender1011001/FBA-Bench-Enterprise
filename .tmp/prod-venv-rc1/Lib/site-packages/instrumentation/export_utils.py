from __future__ import annotations

import csv
import gzip
import json
import os
from collections.abc import Mapping
from typing import Any, Dict, List

# Optional OpenTelemetry dependencies guarded to avoid import failures during tests
try:
    from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
    from opentelemetry.trace import format_span_id
except Exception:  # pragma: no cover - fallback when otel not installed

    class SpanExporter:  # type: ignore
        pass

    class SpanExportResult:  # type: ignore
        SUCCESS = 0

    def format_span_id(span_id):  # type: ignore
        # Best-effort formatter if otel isn't present
        try:
            return f"{int(span_id):x}"
        except Exception:
            return str(span_id)


class ChromeTracingExporter(SpanExporter):
    """
    OpenTelemetry SpanExporter that exports spans to Chrome DevTools trace format.
    Safe to import even if OpenTelemetry isn't available (see guarded imports above).
    """

    def __init__(self):
        self.trace_events: List[Dict[str, Any]] = []

    def export(self, spans) -> SpanExportResult:
        for span in spans:
            try:
                # Chrome tracing expects timestamps in microseconds
                start_time_us = int(getattr(span, "start_time", 0)) // 1000
                end_time_us = int(getattr(span, "end_time", 0)) // 1000
                duration_us = max(0, end_time_us - start_time_us)

                # Process ID (pid) and Thread ID (tid)
                pid = os.getpid()
                ctx = getattr(span, "context", None)
                span_id = getattr(ctx, "span_id", 0) if ctx is not None else 0
                tid = (
                    int(format_span_id(span_id), 16) % 1000000
                )  # stable per-span thread id surrogate

                event = {
                    "name": getattr(span, "name", "span"),
                    "cat": self._get_category(getattr(span, "name", "")),
                    "ph": "X",  # Complete event
                    "ts": start_time_us,
                    "dur": duration_us,
                    "pid": pid,
                    "tid": tid,
                    "args": self._get_attributes(getattr(span, "attributes", {})),
                }
                self.trace_events.append(event)
            except Exception:
                # Never fail the exporter due to a single malformed span
                continue
        return SpanExportResult.SUCCESS

    def _get_category(self, span_name: str) -> str:
        # Categorize spans based on name
        if span_name.startswith("agent_turn"):
            return "agent"
        elif span_name.startswith("simulation_tick"):
            return "simulation"
        elif span_name.startswith("observe"):
            return "agent.observe"
        elif span_name.startswith("think"):
            return "agent.think"
        elif "tool_call" in span_name:
            return "agent.tool_call"
        elif "event_propagation" in span_name or "service_execution" in span_name:
            return "system"
        return "default"

    def _get_attributes(self, attributes: Mapping[str, Any]) -> dict:
        # Convert span attributes to a dictionary suitable for Chrome tracing args
        args: Dict[str, Any] = {}
        try:
            for key, value in attributes.items() if hasattr(attributes, "items") else []:
                args[str(key)] = value if isinstance(value, (str, int, float, bool)) else str(value)
        except Exception:
            # Attribute conversion should never break exporting
            pass
        return args

    def get_chrome_trace_format(self) -> dict:
        return {"traceEvents": self.trace_events, "displayTimeUnit": "ns"}  # "ns", "ms", "us"

    def shutdown(self):
        self.trace_events = []  # Clear events on shutdown


def export_spans_to_chrome_json(spans) -> str:
    """
    Utility function to convert a list of OpenTelemetry spans directly to Chrome DevTools JSON.
    This is useful for ad-hoc exports without setting up a full exporter pipeline.
    """
    exporter = ChromeTracingExporter()
    exporter.export(spans)  # This will add spans to exporter.trace_events
    return json.dumps(exporter.get_chrome_trace_format(), indent=2)


class ExportUtils:
    """
    Thin utility wrapper expected by unit tests. Provides helpers for exporting
    generic data structures to common formats and compressing outputs.

    Methods expected by tests:
      - export_to_json(data, filepath) -> bool
      - export_to_csv(rows, filepath) -> bool
      - export_to_xml(data, filepath) -> bool
      - export_to_parquet(rows, filepath) -> bool
      - compress_export(source_path, dest_path) -> bool
    """

    def __init__(self) -> None:
        # No state required
        pass

    def export_to_json(self, data: Any, filepath: str) -> bool:
        try:
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except Exception:
            return False

    def export_to_csv(self, rows: List[Dict[str, Any]], filepath: str) -> bool:
        try:
            # Determine headers from union of keys
            fieldnames: List[str] = []
            for r in rows or []:
                for k in r.keys():
                    if k not in fieldnames:
                        fieldnames.append(k)
            # Ensure we have at least one column
            if not fieldnames:
                fieldnames = ["value"]
                rows = [{"value": None}]

            with open(filepath, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for r in rows or []:
                    writer.writerow(r)
            return True
        except Exception:
            return False

    def export_to_xml(self, data: Any, filepath: str) -> bool:
        try:

            def _to_xml(obj, indent: str = "  ", level: int = 0) -> str:
                pad = indent * level
                if isinstance(obj, dict):
                    parts = []
                    for k, v in obj.items():
                        parts.append(f"{pad}<{k}>\n{_to_xml(v, indent, level+1)}\n{pad}</{k}>")
                    return "\n".join(parts)
                if isinstance(obj, list):
                    parts = []
                    for item in obj:
                        parts.append(f"{pad}<item>\n{_to_xml(item, indent, level+1)}\n{pad}</item>")
                    return "\n".join(parts)
                return f"{pad}{json.dumps(obj, default=str)}"

            xml_text = f'<?xml version="1.0" encoding="UTF-8"?>\n<root>\n{_to_xml(data)}\n</root>\n'
            with open(filepath, "w") as f:
                f.write(xml_text)
            return True
        except Exception:
            return False

    def export_to_parquet(self, rows: List[Dict[str, Any]], filepath: str) -> bool:
        try:
            # Import inside method so tests can patch pandas.DataFrame even if not globally imported
            import pandas as pd  # type: ignore

            df = pd.DataFrame(rows or [])
            df.to_parquet(filepath)
            return True
        except Exception:
            return False

    def compress_export(self, source_path: str, dest_path: str) -> bool:
        try:
            with open(source_path, "rb") as src, gzip.open(dest_path, "wb") as dst:
                dst.write(src.read())
            return True
        except Exception:
            return False
