"""
This module provides functionality for evaluating and grading LLM answers based
on pre-defined criteria.
"""

from epam.auto_llm_eval.evaluator import GradingResult
from epam.auto_llm_eval.evaluator import evaluate_scenario
from epam.auto_llm_eval.evaluator import grade_scenario
from epam.auto_llm_eval.evaluator import read_file
from epam.auto_llm_eval.evaluator import write_file

__all__ = [
    "GradingResult",
    "evaluate_scenario",
    "grade_scenario",
    "read_file",
    "write_file",
]
