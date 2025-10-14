"""
Evaluation module for FBA-Bench.

This module provides comprehensive evaluation capabilities for assessing agent performance
across multiple dimensions, including comparative analysis, trend analysis, and statistical
validation.
"""

from .enhanced_evaluation_framework import (
    DimensionScore,
    DimensionWeight,
    EnhancedEvaluationFramework,
    EvaluationConfig,
    EvaluationDimension,
    EvaluationGranularity,
    EvaluationProfile,
    MultiDimensionalEvaluation,
)

__all__ = [
    "EnhancedEvaluationFramework",
    "EvaluationDimension",
    "EvaluationGranularity",
    "DimensionWeight",
    "EvaluationConfig",
    "DimensionScore",
    "MultiDimensionalEvaluation",
    "EvaluationProfile",
]
