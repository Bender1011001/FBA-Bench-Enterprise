"""
Lightweight instrumentation package shim.
"""
from .tracer import setup_tracing
__all__ = ["setup_tracing"]