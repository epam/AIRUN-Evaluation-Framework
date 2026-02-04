"""This module provides functionality for evaluating and grading LLM answers"""

import json
import logging
import re
import textwrap
import os
import yaml


from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Generator,Self


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
    - type: the criterion type.
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
      type: completeness
    - criterion: Verify the function has a docstring
      weight: 0.5
      type: completeness
    - Verify the function has type hints
      weight: 0.5
      type: completeness
    - Ensure the code is elegant
      weight: 0.25
      type: accuracy

    EVALUATION REPORT:
    {{
      "evaluation_steps": [
        {{"criterion": "Verify the function code is written in Python", "weight": 1.0, "type": "completeness", "passed": true, "confidence": 100, "explanation": "The function is clearly written in Python syntax."}},
        {{"criterion": "Verify the function has a docstring", "weight": 0.5, "type": "completeness", "passed": true, "confidence": 100, "explanation": "The function includes a docstring that describes its purpose, arguments, and return value."}},
        {{"criterion": "Verify the function has type hints", "weight": 0.5, "type": "completeness", "passed": false, "confidence": 100, "explanation": "The function does not include type hints for its parameters or return type."}},
        {{"criterion": "Ensure the code is elegant", "weight": 0.25, "type": "accuracy", "passed": true, "confidence": 90, "explanation": "The code is simple and straightforward, but could be improved with type hints."}}
      ]
    }}

    Now, evaluate the following and provide the evaluation report in the specified JSON format:

    ANSWER:

    {answer}

    EVALUATION STEPS:

    {steps}
    '''
)


VALID_RESULT_IDETIFIER_PATTERN = re.compile('^\\w+$')

def assert_valid_result_identifier(id_: str) -> None:
    if not VALID_RESULT_IDETIFIER_PATTERN.match(id_):
        raise ValueError(f"'{id_}' is not a valid result identifier. It should only contains alphanumeric letters (a-z) and (0-9), or underscores (_).")


class CriterionEvalStep:
    criterion: str
    weight: float
    type: str

    def __init__(self, criterion: str, weight: float, type: str):
        self.criterion = criterion
        self.weight = weight
        self.type = type


class CriterionEvalStepProcessed(CriterionEvalStep):
    passed: bool
    confidence: float
    explanation: str

    def __init__(
        self, criterion: str, weight: float, type: str, passed: bool, confidence: float, explanation: str
    ):
        super().__init__(criterion, weight, type)
        self.passed = passed
        self.confidence = confidence
        self.explanation = explanation


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


class EvaluationStepsBucket:
    name: str
    evaluation_steps: tuple[CriterionEvalStep, ...]

    def __init__(self, name: str, evaluation_steps: tuple[CriterionEvalStep, ...]):
        self.name = name
        self.evaluation_steps = evaluation_steps


class CriteriaBase(ABC):
    __metadata: CriteriaMeta
    __criterion_eval_steps: tuple[CriterionEvalStep, ...]

    def __init__(
        self, metadata: CriteriaMeta, criterion_eval_steps: tuple[CriterionEvalStep, ...]
    ):
        self.__metadata = metadata
        self.__criterion_eval_steps = criterion_eval_steps

    @property
    def metadata(self):
        return self.__metadata

    @property
    def criterion_eval_steps(self):
        return self.__criterion_eval_steps


    @abstractmethod
    def evaluation_steps_buckets(self) -> Generator[EvaluationStepsBucket, None, None]:
        """Return iterator of EvaluationStepsBucket to evaluate."""
        pass


class Criteria(CriteriaBase):

    def __init__(
        self, metadata: CriteriaMeta, criterion_eval_steps: tuple[CriterionEvalStep, ...]
    ):
        super().__init__(metadata, criterion_eval_steps)

    @classmethod
    def from_yaml(cls, yaml_content: str) -> Self:
        data = yaml.safe_load(yaml_content)

        if "evaluation_steps" not in data or "metadata" not in data:
            raise ValueError(
                "YAML must contain 'evaluation_steps' and 'metadata' sections."
            )

        data_eval_steps = data["evaluation_steps"]
        criterion_eval_steps = []

        for type_ in data_eval_steps:
            for item in data_eval_steps[type_]:
                if "criterion" not in item or "weight" not in item:
                    raise ValueError(
                        "Each step must have 'criterion' and 'weight'."
                    )

                criterion_eval_steps.append(
                    CriterionEvalStep(
                        criterion=item["criterion"], weight=float(item["weight"]), type=type_
                    )
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

        return cls(metadata=metadata, criterion_eval_steps=tuple(criterion_eval_steps))

    def evaluation_steps_buckets(self) -> Generator[EvaluationStepsBucket, None, None]:
        distinct_types = {step.type for step in self.criterion_eval_steps}
        for type_ in distinct_types:
            typed_evaluation_steps = tuple(step for step in self.criterion_eval_steps if step.type == type_)
            yield EvaluationStepsBucket(name=type_, evaluation_steps=typed_evaluation_steps)


class EvaluationResult:
    __name: str
    __report: str

    def __init__(self, name: str, report: str):
        assert_valid_result_identifier(name)
        self.__name = name
        self.__report = report

    @property
    def name(self):
        return self.__name

    @property
    def report(self):
        return self.__report


class GradeResult:
    __name: str
    __evaluation_steps: tuple[CriterionEvalStepProcessed]

    def __init__(self, name: str, evaluation_steps: tuple[CriterionEvalStepProcessed]):
        assert_valid_result_identifier(name)
        self.__name = name
        self.__evaluation_steps = evaluation_steps

    @property
    def name(self):
        return self.__name

    @property
    def evaluation_steps(self):
        return self.__evaluation_steps

    @classmethod
    def from_evaluation_result(cls, evaluation_result: EvaluationResult) -> Self:
        """
        Construct grade result object from the evaluation report.

        Args:
            evaluation_result (str): The evaluation result to be graded.

        Returns:
            GradeResult: An object containing the grading result.

        Raises:
            TypeError: If the evaluation report is in wrong format.
        """

        try:
            result_evaluation_steps = []
            report_json = json.loads(evaluation_result.report)
            evaluation_steps = report_json.get("evaluation_steps")
            for item in evaluation_steps:
                criterion = item.get("criterion")
                weight = float(item.get("weight"))
                type_ = item.get("type")
                passed = bool(item.get("passed"))
                confidence = float(item.get("confidence"))
                explanation = item.get("explanation")
                eval_step_obj = CriterionEvalStepProcessed(
                    criterion=criterion,
                    weight=weight,
                    type=type_,
                    passed=passed,
                    confidence=confidence,
                    explanation=explanation,
                )
                result_evaluation_steps.append(eval_step_obj)
            return cls(evaluation_result.name, tuple(result_evaluation_steps))
        except (json.JSONDecodeError, TypeError, ValueError, AttributeError) as e:
            raise TypeError(f"Invalid evaluation report: {e}")

    def get_score(self) -> float:
        """
        Calculate and return the overall score based on criterion evaluations.

        The score is calculated as the weighted sum of passed criterion divided
        by the total weight of all criterion.

        Returns:
            float: The overall score as a float between 0 and 1.
        """
        total_weight = sum(c.weight for c in self.__evaluation_steps)
        if total_weight == 0:
            return 0.0
        passed_weight = sum(
            c.weight for c in self.__evaluation_steps if c.passed
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
    evaluation_steps: tuple[CriterionEvalStep, ...],
    output: str,
    execute_prompt: Callable[[str], str],
) -> str:
    """
    Evaluate the answer based on the provided evaluation steps.

    This function generates an evaluation report for a given answer using
    specified evaluation steps and a callable evaluation function.

    Args:
      evaluation_steps (tuple[CriterionEvalStep, ...]): A tuple of steps to be used in evaluating
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
            f"- criterion: {item.criterion}\n  weight: {item.weight}\n  type: {item.type}\n"
        )
    prompt: str = EVALUATION_PROMPT.format(answer=output, steps=criterion_str)
    report: str = execute_prompt(prompt)

    return report


def evaluate_scenario(
    criteria: Criteria,
    output: str,
    execute_prompt: Callable[[str], str],
) -> tuple[EvaluationResult, ...]:
    """
    Evaluate a single scenario.
    This function accepts the scenario data and evaluates it against specified criteria of various types, typically completeness and accuracy.

    Args:
        criteria (Criteria): Evaluation criteria.
        output (str): Scenario output.
        execute_prompt (Callable[[str], str]): The function to execute the evaluation prompt.

    Returns:
        tuple[EvaluationResult, ...]: A tuple containing the evaluation results.
    """
    reports = []
    for evaluation_steps_bucket in criteria.evaluation_steps_buckets():
        logger.info('evaluate_output')
        report = evaluate_output(
            evaluation_steps_bucket.evaluation_steps,
            output,
            execute_prompt,
        )
        reports.append(EvaluationResult(evaluation_steps_bucket.name, report))

    return tuple(reports)


def grade_scenario(evaluation_results: tuple[EvaluationResult, ...]) -> tuple[GradeResult, ...]:
    """
    Grade reports.

    Args:
        evaluation_results tuple(EvaluationResult, ...): The evaluation results to be graded.

    Returns:
        tuple[GradeResult, ...]: A tuple containing the grading results.
    """
    results = tuple(GradeResult.from_evaluation_result(result) for result in evaluation_results)

    return results
