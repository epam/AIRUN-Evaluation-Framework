"""
This module provides functionality for evaluating and grading LLM answers based
on pre-defined criteria.
"""

from epam.auto_llm_eval.evaluator import EvaluationResult
from epam.auto_llm_eval.evaluator import evaluate_scenario
from epam.auto_llm_eval.evaluator import evaluate_metric
from epam.auto_llm_eval.evaluator import grade_metric

__all__ = [
    "EvaluationResult",
    "evaluate_scenario",
    "evaluate_metric",
    "grade_metric"
]
