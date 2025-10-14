"""
Skill Module Framework for FBA-Bench Multi-Domain Agent Capabilities.

This module provides:
- Legacy event-driven domain skills (BaseSkill etc.) used by Multi-Skill Agents.
- A lightweight, deterministic Skill system with a uniform run/arun contract and a registry,
  intended for simple, dependency-light skills callable by agents/runners.

Exports (legacy):
    - BaseSkill: Abstract base class for legacy domain skill modules
    - SupplyManagerSkill: Inventory and supplier management capabilities
    - MarketingManagerSkill: Advertising and pricing strategy capabilities
    - CustomerServiceSkill: Customer interaction and satisfaction capabilities
    - FinancialAnalystSkill: Budget management and financial planning capabilities

Exports (lightweight skills system):
    - Skill, SkillExecutionError
    - register, create, list_skills
    - Built-in skills: CalculatorSkill, SummarizeSkill, ExtractFieldsSkill, LookupSkill, TransformTextSkill
"""

# Legacy multi-skill exports (kept for compatibility)
# Lightweight skills framework exports
from .base import Skill, SkillExecutionError
from .base_skill import BaseSkill
from .calculator import CalculatorSkill
from .customer_service import CustomerServiceSkill
from .extract_fields import ExtractFieldsSkill
from .financial_analyst import FinancialAnalystSkill
from .lookup import LookupSkill
from .marketing_manager import MarketingManagerSkill
from .registry import create, list_skills, register
from .summarize import SummarizeSkill
from .supply_manager import SupplyManagerSkill
from .transform_text import TransformTextSkill

__all__ = [
    # Legacy
    "BaseSkill",
    "SupplyManagerSkill",
    "MarketingManagerSkill",
    "CustomerServiceSkill",
    "FinancialAnalystSkill",
    # Lightweight skills framework
    "Skill",
    "SkillExecutionError",
    "register",
    "create",
    "list_skills",
    "CalculatorSkill",
    "SummarizeSkill",
    "ExtractFieldsSkill",
    "LookupSkill",
    "TransformTextSkill",
]
