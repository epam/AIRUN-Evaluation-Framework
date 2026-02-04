"""This module provides functionality for evaluating and grading LLM answers"""

import json
import os
import logging
import yaml
import textwrap
from pathlib import Path
from typing import Callable, List, Self, Tuple


logger = logging.getLogger(__name__)

EVALUATION_PROMPT = textwrap.dedent(
    '''
    Your task is to evaluate the answer according to the evaluation steps.
    Evaluate only that the answer meets the evaluation steps, do not make
    any assumptions about the task/experiment conditions or the missing
    context/images (trust that everything was provided to the task executor).

    Output must be a valid JSON document containing evaluation report.
    Return only JSON starting with {{ and ending with }}.
    Do not add any comments to JSON document.

    Evaluation report contains list of evaluated steps.
    Each step contains the following fields: criterion, weight, passed, confidence, explanation.
    - criterion: The evaluation criterion text as provided in the input.
    - weight: The weight of the criterion as provided in the input.
    - passed: true if the answer meets the criterion, false otherwise.
    - confidence: Your confidence level in the evaluation result as a percentage (0-100%).
    - explanation: Explanation of the evaluation result, especially if confidence is less than 100%.

    Here's an example of an answer and its evaluation response:

    ANSWER:

    ```python
    def sum_integers(a, b):
        """
        Sum two integers and return the result.

        Args:
            a: The first integer.
            b: The second integer.

        Returns the sum of the two input integers.
        """
        return a + b
    ```

    EVALUATION STEPS:

    - criterion: Verify the function code is written in Python
      weight: 1.0
    - criterion: Verify the function has a docstring
      weight: 0.5
    - Verify the function has type hints
      weight: 0.5
    - Ensure the code is elegant
      weight: 0.25

    EVALUATION REPORT:
    {{
      "evaluation_steps": [
        {{"criterion": "Verify the function code is written in Python", "weight": 1.0, "passed": true, "confidence": 100, "explanation": "The function is clearly written in Python syntax."}},
        {{"criterion": "Verify the function has a docstring", "weight": 0.5, "passed": true, "confidence": 100, "explanation": "The function includes a docstring that describes its purpose, arguments, and return value."}},
        {{"criterion": "Verify the function has type hints", "weight": 0.5, "passed": false, "confidence": 100, "explanation": "The function does not include type hints for its parameters or return type."}},
        {{"criterion": "Ensure the code is elegant", "weight": 0.25, "passed": true, "confidence": 90, "explanation": "The code is simple and straightforward, but could be improved with type hints."}}
      ]
    }}

    Now, evaluate the following and provide the evaluation report in the specified JSON format:

    ANSWER:

    {answer}

    EVALUATION STEPS:

    {steps}
    '''
)


class CriterionEvalStep:
    criterion: str
    weight: float

    def __init__(self, criterion: str, weight: float):
        self.criterion = criterion
        self.weight = weight


class CriterionEvalStepProcessed(CriterionEvalStep):
    passed: bool
    explanation: str

    def __init__(
        self, criterion: str, weight: float, passed: bool, explanation: str
    ):
        super().__init__(criterion, weight)
        self.passed = passed
        self.explanation = explanation


class CriterionEvalSteps:
    accuracy: List[CriterionEvalStep]
    completeness: List[CriterionEvalStep]

    def __init__(
        self,
        accuracy: List[CriterionEvalStep],
        completeness: List[CriterionEvalStep],
    ):
        self.accuracy = accuracy
        self.completeness = completeness


class CriteriaMeta:
    category: str
    experiment: str
    repository: str
    scenario_id: int

    def __init__(
        self, category: str, experiment: str, repository: str, scenario_id: int
    ):
        self.category = category
        self.experiment = experiment
        self.repository = repository
        self.scenario_id = scenario_id


class Criteria:
    evaluation_steps: CriterionEvalSteps
    metadata: CriteriaMeta

    def __init__(
        self, evaluation_steps: CriterionEvalSteps, metadata: CriteriaMeta
    ):
        self.evaluation_steps = evaluation_steps
        self.metadata = metadata

    @staticmethod
    def from_yaml(yaml_content: str) -> Self:
        data = yaml.safe_load(yaml_content)

        if "evaluation_steps" not in data or "metadata" not in data:
            raise ValueError(
                "YAML must contain 'evaluation_steps' and 'metadata' sections."
            )

        eval_steps = data["evaluation_steps"]
        accuracy_steps = []
        completeness_steps = []

        if "accuracy" not in eval_steps or "completeness" not in eval_steps:
            raise ValueError(
                "YAML 'evaluation_steps' must contain 'accuracy' and 'completeness'."
            )

        for item in eval_steps["accuracy"]:
            if "criterion" not in item or "weight" not in item:
                raise ValueError(
                    "Each accuracy step must have 'criterion' and 'weight'."
                )

            accuracy_steps.append(
                CriterionEvalStep(
                    criterion=item["criterion"], weight=float(item["weight"])
                )
            )

        for item in eval_steps["completeness"]:
            if "criterion" not in item or "weight" not in item:
                raise ValueError(
                    "Each completeness step must have 'criterion' and 'weight'."
                )

            completeness_steps.append(
                CriterionEvalStep(
                    criterion=item["criterion"], weight=float(item["weight"])
                )
            )

        steps = CriterionEvalSteps(
            accuracy=accuracy_steps, completeness=completeness_steps
        )

        meta = data["metadata"]
        required_meta = ["category"]
        for key in required_meta:
            if key not in meta:
                raise ValueError(f"Metadata missing required field: {key}")

        metadata = CriteriaMeta(
            category=meta["category"],
            experiment=meta.get("experiment", ""),
            repository=meta.get("repository", ""),
            scenario_id=int(meta.get("scenario_id", -1)),
        )

        return Criteria(evaluation_steps=steps, metadata=metadata)


class GradingResult:
    evaluation_steps: List[CriterionEvalStepProcessed]

    def __init__(self):
        """
        Initialize an EvaluationResult instance.

        Initializes an empty list for probabilities and an empty dictionary
        for metadata.
        """
        self.evaluation_steps = []

    def add_eval_step(self, eval_step: CriterionEvalStepProcessed) -> None:
        """
        Add a criterion evaluation result to the grading result.

        Args:
            criterion (CriterionEval): The criterion evaluation result to add.
        """
        self.evaluation_steps.append(eval_step)

    def get_score(self) -> float:
        """
        Calculate and return the overall score based on criterion evaluations.

        The score is calculated as the weighted sum of passed criterion divided
        by the total weight of all criterion.

        Returns:
            float: The overall score as a float between 0 and 1.
        """
        total_weight = sum(c.weight for c in self.evaluation_steps)
        if total_weight == 0:
            return 0.0
        passed_weight = sum(
            c.weight for c in self.evaluation_steps if c.passed
        )
        score = passed_weight / total_weight

        return score


def read_file(file_path: str | Path) -> str:
    """
    Read the content of a file and return it as a string.

    This function opens the specified file, reads its entire content,
    and returns it as a string. It uses UTF-8 encoding to handle
    various character sets.

    Args:
        file_path (str): The path to the file to be read.

    Returns:
        str: The content of the file as a string.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        IOError: If there's an error reading the file.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return content


def write_file(file_path: str | Path, content: str) -> None:
    """
    Write the content to a file.

    This function opens the specified file in write mode and writes the given
    content to it. It first converts the file path to absolute and checks that
    the parent directory exists.

    It uses UTF-8 encoding to handle various character sets.

    Args:
        file_path (str): The path to the file where the content will be
        written.
        content (str): The content to be written to the file.

    Raises:
        IOError: If there's an error writing to the file.
        FileNotFoundError: If the parent directory does not exist.
    """
    abs_path = os.path.abspath(os.path.expanduser(file_path))
    parent_dir = os.path.dirname(abs_path)

    if not os.path.exists(parent_dir):
        raise FileNotFoundError(
            f"Parent directory does not exist: {parent_dir}"
        )

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)


def evaluate_output(
    evaluation_steps: List[CriterionEvalStep],
    output: str,
    execute_prompt: Callable[[str], str],
) -> str:
    """
    Evaluate the answer based on the provided evaluation steps.

    This function generates an evaluation report for a given answer using
    specified evaluation steps and a callable evaluation function.

    Args:
      evaluation_steps (List[EvalStep]): A list of steps to be used in evaluating
      the output.
      output (str): The output to be evaluated.
      execute_prompt (callable): A function that accepts a string prompt and returns a string report.

    Returns:
      str: The evaluation report generated by the evaluation function.

    Raises:
      ValueError: If the evaluation_steps list is empty.
      TypeError: If evaluate is not callable.
    """
    if not evaluation_steps:
        raise ValueError("Evaluation steps cannot be empty.")
    if not callable(execute_prompt):
        raise TypeError(
            "evaluate must be a callable accepting a string and returning a string."
        )

    criterion_str = ""
    for item in evaluation_steps:
        criterion_str += (
            f"- criterion: {item.criterion}\n  weight: {item.weight}\n"
        )
    prompt: str = EVALUATION_PROMPT.format(answer=output, steps=criterion_str)
    report: str = execute_prompt(prompt)

    return report


def grade_report(evaluation_report: str) -> GradingResult:
    """
    Grade the answer based on the evaluation report.

    Args:
        evaluation_report (str): The evaluation report to be graded.

    Returns:
        GradingResult: An object containing the grading result.

    Raises:
        TypeError: If the evaluation report is in wrong format.
    """

    result = GradingResult()
    try:
        report_json = json.loads(evaluation_report)
        evaluation_steps = report_json.get("evaluation_steps")
        for item in evaluation_steps:
            criterion = item.get("criterion")
            weight = float(item.get("weight"))
            passed = bool(item.get("passed"))
            explanation = item.get("explanation")
            eval_step_obj = CriterionEvalStepProcessed(
                criterion=criterion,
                weight=weight,
                passed=passed,
                explanation=explanation,
            )
            result.add_eval_step(eval_step_obj)
    except (json.JSONDecodeError, TypeError, ValueError, AttributeError) as e:
        raise TypeError(f"Invalid evaluation report: {e}")

    return result


def evaluate_scenario(
    criteria: Criteria,
    output: str,
    execute_prompt: Callable[[str], str],
) -> Tuple[str, str]:  # [accuracy, completeness]
    """
    Evaluate a single scenario.
    This function accepts the scenario data and evaluates completeness and accuracy.

    Args:
        criteria (Criteria): Evaluation criteria.
        output (str): Scenario output.
        execute_prompt (Callable[[str], str]): The function to execute the evaluation prompt.

    Returns:
        Tuple[EvaluationResult, EvaluationResult]: A tuple containing the
        accuracy and completeness evaluation results.
    """
    completeness_report = evaluate_output(
        criteria.evaluation_steps.completeness,
        output,
        execute_prompt,
    )

    accuracy_report = evaluate_output(
        criteria.evaluation_steps.accuracy, output, execute_prompt
    )

    return (accuracy_report, completeness_report)


def grade_scenario(
    accuracy_report: str, completeness_report: str
) -> Tuple[GradingResult, GradingResult]:
    """
    Grade accuracy and completeness reports.

    Args:
        accuracy_report (str): The accuracy report to be graded.
        completeness_report (str): The completeness report to be graded.

    Returns:
        Tuple[GradingResult, GradingResult]: A tuple containing the
        accuracy and completeness grading results.
    """

    accuracy: GradingResult = grade_report(accuracy_report)
    completeness: GradingResult = grade_report(completeness_report)

    return (accuracy, completeness)
