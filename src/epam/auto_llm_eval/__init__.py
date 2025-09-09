"""
This module provides functionality for evaluating and grading LLM answers based
on pre-defined criteria.
"""

from epam.auto_llm_eval.evaluator import GradingResult
from epam.auto_llm_eval.evaluator import (
    Criteria,
    CriteriaMeta,
    CriteriaEvalStep,
    CriteriaEvalSteps,
    CriteriaEvalStepProcessed,
)
from epam.auto_llm_eval.evaluator import evaluate_output
from epam.auto_llm_eval.evaluator import evaluate_scenario
from epam.auto_llm_eval.evaluator import grade_scenario
from epam.auto_llm_eval.evaluator import read_file
from epam.auto_llm_eval.evaluator import write_file

__all__ = [
    "GradingResult",
    "Criteria",
    "CriteriaMeta",
    "CriteriaEvalStep",
    "CriteriaEvalSteps",
    "CriteriaEvalStepProcessed",
    "evaluate_scenario",
    "evaluate_output",
    "grade_scenario",
    "read_file",
    "write_file",
]
