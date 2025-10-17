"""Performance test suite for FBA-Bench Enterprise.

This module contains performance benchmarks, load tests, and stress tests for critical components.
Tests in this directory focus on:
- System scalability under load
- Response times for key operations
- Resource utilization (CPU, memory, database connections)
- Concurrent execution performance
- End-to-end throughput measurements

All performance tests should be marked with the 'performance' marker and can be run with:
poetry run pytest -m performance -v

Configuration:
- Use realistic production-like data volumes
- Include warm-up phases for accurate measurements
- Report metrics in standardized formats (JSON, CSV)
- Include statistical analysis for reliability
"""
