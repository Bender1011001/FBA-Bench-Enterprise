"""
FBA-Bench Core Models package.

This package contains lightweight, canonical dataclasses used across services.
Submodules:
- competitor: Competitor entity used by services like CompetitorManager
- product: Product entity used by fee/trust/customer event services

Note: Submodule imports are intentionally not performed here to avoid circular
imports during partial repository setup. Import concrete classes from their
respective submodules, e.g.:
    from fba_bench_core.models.competitor import Competitor
    from fba_bench_core.models.product import Product
"""