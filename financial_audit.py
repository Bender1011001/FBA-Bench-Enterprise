"""
Financial audit service shim for integration tests.
This provides a minimal implementation to satisfy imports.
"""

from __future__ import annotations

class FinancialAuditService:
    """Minimal financial audit service implementation."""
    
    def __init__(self):
        self.audits = []
    
    async def audit_transaction(self, transaction_data: dict) -> dict:
        """Audit a transaction."""
        return {"status": "approved", "audit_id": f"audit_{len(self.audits)}"}
    
    async def generate_report(self) -> dict:
        """Generate audit report."""
        return {"total_audits": len(self.audits), "status": "complete"}
