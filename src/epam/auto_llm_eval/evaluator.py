"""This module provides functionality for evaluating and grading LLM answers"""

from typing import Dict, List, Tuple
import os
import logging
from traitlets import Any
import yaml

from langchain_core.messages import HumanMessage
from langchain_core.runnables import Runnable
from langchain_openai import AzureChatOpenAI


import numpy as np

logger = logging.getLogger(__name__)

EVALUATION_PROMPT = '''
    Evaluate the newer according to the evaluation steps.

    Output must be a valid Markdown document containing evaluation report.

    Evaluation report consists of steps which are prefixed with either Pass or
    Fail. Pass means the step passed successfully, Fail means the step is
    Failed. Include your confidence level in the step evaluation as a
    percentage (0-100%) in brackets after each evaluation. 100% means you are
    very confident the step has passed or failed, while 0% means you are not
    confident at all in the result.

    If you are confident less than 100% in the step evaluation result, please
    explain why.

    Include in the end of the report total number of steps evaluated, number of
    passed steps and number of failed steps.

    Here's an example of an answer and its evaluation:

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

    - Verify the function code is written in Python
    - Verify the function has a docstring
    - Verify the function has type hints
    - Ensure the code is elegant

    EVALUATION REPORT:

    # Evaluation Report

    - **Pass** (100%): Verify the function code is written in Python
    - **Pass** (100%): Verify the function has a docstring
    - **Fail** (100%): Verify the function has type hints

        The function `sum_integers` in the provided code does not include type
        hints. We can conclude this by observing the function definition:

        def sum_integers(a, b):

        In Python, type hints are typically added after the parameter names and
        before the colon, followed by the return type hint after the -> symbol.
        The correct format with type hints would look like this:

        def sum_integers(a: int, b: int) -> int:

        The absence of : int after the parameters a and b, and the missing ->
        int before the colon at the end of the function definition, clearly
        indicates that type hints are not present in the given function.

    - **Pass** (90%): Ensure the code is elegant

        The provided function is simple and straightforward, adhering to
        Python's clean and readable syntax. However, incorporating type hints
        could enhance clarity and maintainability, making the code more
        explicit about the expected input and output types.

    ---

    Total steps evaluated: 4
    Number of passed steps: 3
    Number of failed steps: 1

    Now, evaluate the following:

    ANSWER:

    {answer}

    EVALUATION STEPS:

    {steps}

    EVALUATION REPORT:
'''

GRADING_PROMPT = """
    Grade the answer based on the provided evaluation report.

    Grade scale is from 1 to 5 with 1 being the lowest score and 5 being the
    highest.

    Consider the following when grading:
    1. Number of passed vs. failed steps
    2. Severity of failed steps

    Severity levels and examples:
    - Low severity:
      * Minor formatting issues
      * Non-critical TODO comments left in the code
      * Slight deviations in variable naming conventions

    - Medium severity:
      * Missing or incorrect error handling
      * Inefficient algorithms that don't significantly impact performance
      * Incomplete or unclear documentation

    - High severity:
      * Incorrect logic that produces wrong results
      * Security vulnerabilities
      * Failure to implement core functionality
      * Major compatibility issues with specified frameworks/libraries

    Scoring Guide:
    5: All steps passed or only low severity failures
    4: Mostly passed with 1-2 low or one medium severity failures
    3: Several failures, mix of low and medium severity
    2: Multiple failures including 1-2 high severity issues
    1: Majority of steps failed or 3+ critical high severity issues

    EVALUATION REPORT:

    {report}

    Output only one number from 1 to 5 representing the grade.
    """


class EvaluationResult:
    """
    Represents the evaluation result of a metric.

    This class stores and processes probabilities for different scores,
    calculates various score representations, and manages metadata
    associated with the evaluation.
    """

    def __init__(self):
        """
        Initialize an EvaluationResult instance.

        Initializes an empty list for probabilities and an empty dictionary
        for metadata.
        """
        self.probabilities: List[Tuple[int, float]] = []
        self.metadata: Dict[str, Any] = {}

    def set_probabilities(self, top_logprobs: List[dict]) -> None:
        """
        Set probabilities from the LLM response metadata.

        Processes the log probabilities from the LLM response, converting them
        to probabilities for scores 1-5. Ignores tokens that are not in this
        range or have very low probabilities.

        Args:
            top_logprobs (List[dict]): A list of dictionaries containing token
                and logprob information.
        """
        for logprob in top_logprobs:
            token: str = logprob["token"]
            try:
                token_int: int = int(token)
                if token_int not in [1, 2, 3, 4, 5]:
                    raise ValueError("Token is not in the range 1-5")
            except ValueError:
                break

            logprob_value: float = logprob["logprob"]
            probability: float = np.round(np.exp(logprob_value), 2)
            if probability < 0.01:  # Ignore tokens with low probability
                break
            self.probabilities.append((token_int, probability))

    def get_probabilities(self) -> List[Tuple[int, float]]:
        """
        Return the probabilities of the scores.

        Returns:
            List[Tuple[int, float]]: A list of tuples containing score and its
            probability.
        """
        return self.probabilities

    def get_score(self) -> int:
        """
        Return the score with the maximum probability.

        Returns:
            int: The score (1-5) with the highest probability.
        """
        (score, _) = max(self.probabilities, key=lambda x: x[1])
        return score

    def get_weighted_score(self) -> float:
        """
        Return the weighted score based on the probabilities.

        Calculates a weighted average of scores, where each score is weighted
        by its probability.

        Returns:
            float: The weighted score, rounded to two decimal places.
        """
        weighted_score: float = sum(
            [score * prob for (score, prob) in self.probabilities]
        )
        weighted_score = np.round(weighted_score, 2)
        return weighted_score

    def is_confident(self, threshold: float = 0.9) -> bool:
        """
        Determine if the model is confident about the score.

        Args:
            threshold (float, optional): The probability threshold for
            confidence. Defaults to 0.9.

        Returns:
            bool: True if the highest probability exceeds the threshold,
            False otherwise.
        """
        (_, max_prob) = max(self.probabilities, key=lambda x: x[1])
        return max_prob > threshold

    def set_metadata(self, metadata: dict[str, any]) -> None:
        """
        Set metadata for the evaluation result.

        Args:
            metadata (dict[str, any]): A dictionary containing additional
            information about the evaluation.
        """
        self.metadata = metadata

    def to_data_frame(self, metric_name: str) -> dict[str, any]:
        """
        Store the evaluation result as a dataframe row.

        Converts the evaluation result into a dictionary format suitable for
        creating a dataframe row.

        Args:
            metric_name (str): The name of the metric being evaluated.

        Returns:
            dict[str, any]: A dictionary containing evaluation results and
                metadata.
        """
        result_dict: dict[str, any] = {
            "metric": metric_name,
            "score": self.get_score(),
            "weighted_score": self.get_weighted_score(),
            "is_confident": self.is_confident(),
        }

        prob_dict: dict[str, float] = {
            f"score_{grade}": prob for grade, prob in self.probabilities
        }

        merged_dict: dict[str, any] = {
            **result_dict,
            **prob_dict,
            **self.metadata
        }

        return merged_dict


def read_file(file_path: str) -> str:
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


def write_file(file_path: str, content: str) -> None:
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


def evaluate_metric(
    evaluation_steps: List[str],
    answer: str,
    model: Runnable
) -> str:
    """
    Evaluate the answer based on the provided evaluation steps.

    This function generates an evaluation report for a given answer using
    specified evaluation steps and an AI model.

    Args:
        evaluation_steps (List[str]): A list of steps to be used in evaluating
        the answer.
        answer (str): The answer to be evaluated.
        model (Runnable): The AI model used for generating the
        evaluation.

    Returns:
        str: The evaluation report generated by the AI model.

    Raises:
        ValueError: If the evaluation_steps list is empty.
        TypeError: If the model is not an instance of Runnable.
    """
    if not evaluation_steps:
        raise ValueError("Evaluation steps cannot be empty.")
    if not isinstance(model, Runnable):
        raise TypeError("Model must be an instance of Runnable.")

    prompt: str = EVALUATION_PROMPT.format(
        answer=answer, steps="\n".join(evaluation_steps)
    )

    message: HumanMessage = HumanMessage(content=prompt)

    api_response = model.invoke([message])
    report: str = api_response.content

    return report


def grade_metric(
    evaluation_report: str,
    model: Runnable
) -> EvaluationResult:
    """
    Grade the answer based on the evaluation report.

    This function uses an AI model to grade the evaluation report and return
    an EvaluationResult object containing the grading probabilities.

    Args:
        evaluation_report (str): The evaluation report to be graded.
        model (Runnable): The AI model used for grading.

    Returns:
        EvaluationResult: An object containing the grading probabilities.

    Raises:
        TypeError: If the model is not an instance of Runnable.
    """
    if not isinstance(model, Runnable):
        raise TypeError("Model must be an instance of Runnable.")

    prompt: str = GRADING_PROMPT.format(report=evaluation_report)
    message: HumanMessage = HumanMessage(content=prompt)

    api_response: Any = model.invoke([message])
    top_five_logprobs: Dict[str, float] = (
        api_response.response_metadata.get("logprobs", {})
        .get("content", [{}])[0]
        .get("top_logprobs", {})
    )
    result: EvaluationResult = EvaluationResult()
    result.set_probabilities(top_five_logprobs)

    return result


def get_scenario_file(base_path: str, scenario_id: str, filename: str) -> str:
    """
    Get the content of a scenario file with validation.

    Args:
        base_path (str): The base path to the scenario files.
        scenario_id (str): The ID of the scenario.
        filename (str): Name of the file to read.

    Returns:
        str: Content of the file.

    Raises:
        FileNotFoundError: If the file or directory doesn't exist.
    """
    file_path = os.path.abspath(os.path.join(base_path, scenario_id, filename))
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    return read_file(file_path)


def evaluate_scenario(
    base_path: str,
    scenario_id: str,
    evaluation_model: AzureChatOpenAI,
    grading_model: AzureChatOpenAI
) -> Tuple[EvaluationResult, EvaluationResult]:
    """
    Evaluate a single scenario from a dataset.

    This function reads the scenario data, evaluates completeness and accuracy,
    and grades the evaluation reports.

    Args:
        base_path (str): The base path to the scenario files.
        scenario_id (str): The ID of the scenario to evaluate.
        model (AzureChatOpenAI): The AI model used for evaluation and grading.

    Returns:
        Tuple[EvaluationResult, EvaluationResult]: A tuple containing the
        accuracy and completeness evaluation results.
    """
    output: str = get_scenario_file(
        base_path, scenario_id, "output.md"
    )
    metadata_content: str = get_scenario_file(
        base_path, scenario_id, "meta.yaml"
    )
    metadata: Dict[str, Any] = yaml.safe_load(metadata_content)
    meta: Dict[str, Any] = metadata.get("metadata", {})
    evaluation_steps: Dict[str, List[str]] = metadata.get(
        "evaluation_steps", {}
    )

    completeness_evaluation_steps: List[str] = evaluation_steps.get(
        "completeness", []
    )
    accuracy_evaluation_steps: List[str] = evaluation_steps.get(
        "accuracy", []
    )

    print(f"Evaluating scenario {scenario_id}_{meta.get('scenario_name')}")

    completeness_report: str = evaluate_metric(
        completeness_evaluation_steps, output, evaluation_model
    )

    try:
        write_file(
            os.path.join(base_path, scenario_id, "completeness.md"),
            completeness_report,
        )
    except FileNotFoundError:
        logger.error(
            "Scenario directory not found: %s/%s. "
            "Skipping completeness report.",
            base_path,
            scenario_id
        )
    except OSError as e:
        logger.error(
            "Failed to write completeness report for scenario %s: %s",
            scenario_id,
            e
        )

    accuracy_report: str = evaluate_metric(
        accuracy_evaluation_steps, output, evaluation_model
    )

    try:
        write_file(
            os.path.join(base_path, scenario_id, "accuracy.md"),
            accuracy_report,
        )
    except FileNotFoundError:
        logger.error(
            "Scenario directory not found: %s/%s. "
            "Skipping accuracy report.",
            base_path,
            scenario_id
        )
    except OSError as e:
        logger.error(
            "Failed to write accuracy report for scenario %s: %s",
            scenario_id,
            e
        )

    model_with_logprobs: AzureChatOpenAI = grading_model.bind(
        logprobs=True
    ).bind(
        top_logprobs=5
    )

    print(f"Grading scenario {scenario_id}_{meta.get('scenario_name')}")
    accuracy: EvaluationResult = grade_metric(
        accuracy_report, model_with_logprobs
    )
    accuracy.set_metadata(meta)

    completeness: EvaluationResult = grade_metric(
        completeness_report, model_with_logprobs
    )
    completeness.set_metadata(meta)

    return (accuracy, completeness)
