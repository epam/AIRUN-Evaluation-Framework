"""Evaluate a single scenario from a dataset in a new format"""

import os
import argparse
import logging

import pandas as pd

from langchain_openai import AzureChatOpenAI, ChatOpenAI

from epam.auto_llm_eval import evaluate_scenario

logger = logging.getLogger(__name__)


def get_gpt4_model():
    """Get the GPT-4 model."""
    # Specify configuration for the AI Dial endpoint
    openai_endpoint = "https://ai-proxy.lab.epam.com"
    openai_deploymet_name = "gpt-4o-2024-05-13"
    openai_api_version = "2024-05-01-preview"

    # Read API key from the environment variables
    azure_api_key = os.environ["AZURE_API_KEY"]
    if not azure_api_key:
        raise ValueError("AZURE_API_KEY environment variable is not set")

    # Define GPT-4-omni model
    model = AzureChatOpenAI(
        temperature=0,  # request deterministic behavior
        azure_endpoint=openai_endpoint,
        azure_deployment=openai_deploymet_name,
        api_version=openai_api_version,
        api_key=azure_api_key,
    )

    return model


def get_o1_mini_model():
    """Get the o1-mini model for generating evaluation reports."""
    # Read API key from the environment variables
    openai_api_key = os.environ["OPENAI_API_KEY"]
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    # Define o1-mini model
    model = ChatOpenAI(
        model_name="o1-mini",
        temperature=1,
        api_key=openai_api_key,
    )

    return model


def save_grading_report(report_path: str, report):
    """Save the grading report to a file."""
    df = pd.DataFrame(report)
    df.to_csv(report_path, index=False)


def parse_scenarios_ranges(scenarios_ranges: str):
    """Parse scenarios ranges. Sample: 1,3,5-10"""
    result = set()
    for part in scenarios_ranges.split(","):
        x = part.split("-")
        result.update(range(int(x[0]), int(x[-1]) + 1))
    return sorted(result)


def validate_data_path(path: str) -> str:
    """Validate and normalize a data directory path."""
    if not path:
        raise ValueError("Data directory path cannot be empty")

    # Convert to absolute path and normalize separators
    abs_path = os.path.abspath(os.path.expanduser(path))

    # Check if path exists for required paths
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Data directory does not exist: {abs_path}")

    # Check if path is a directory
    if not os.path.isdir(abs_path):
        raise ValueError(f"Data directory is not a directory: {abs_path}")

    return abs_path


def validate_report_path(path: str) -> str:
    """Validate and normalize a report file path."""
    if not path:
        raise ValueError("Report path cannot be empty")

    # Convert to absolute path and normalize separators
    abs_path = os.path.abspath(os.path.expanduser(path))

    # Check if path does not exist
    if os.path.exists(abs_path):
        raise FileExistsError(f"Grading report already exists: {abs_path}")

    # Check if the parent directory exists
    parent_dir = os.path.dirname(abs_path)
    if not os.path.exists(parent_dir):
        raise FileNotFoundError(
            f"Parent directory for grading report does not exist: {parent_dir}"
        )

    # Check if path has .csv extension
    if not abs_path.endswith(".csv"):
        raise ValueError(f"Report must be in CSV format: {abs_path}")

    return abs_path


def is_valid_scenario(
    filename: str,
    data_dir: str,
    scenarios: list[int]
) -> bool:
    """Check if the given filename represents a valid scenario to evaluate.

    Args:
        filename: Name of the directory to check
        data_dir: Base directory path
        scenarios: List of scenario numbers to evaluate

    Returns:
        bool: True if the directory is a valid scenario to evaluate
    """
    # Check if it's a directory
    scenario_dir = os.path.join(data_dir, filename)
    if not os.path.isdir(scenario_dir):
        return False

    # Check if scenario name is a number
    if not filename.isdigit():
        return False

    # Check if scenario number is in the requested range
    if int(filename) not in scenarios:
        return False

    # Check required files present in the scenario directory
    required_files = ['input.txt', 'meta.yaml', 'output.md']
    for required_file in required_files:
        file_path = os.path.join(scenario_dir, required_file)
        if not os.path.isfile(file_path):
            logger.warning(
                "Scenario %s is missing required file: %s",
                filename,
                required_file
            )
            return False

    return True


def main():
    """Main function to evaluate the scenarios."""
    parser = argparse.ArgumentParser(
        description="Evaluate benchmark scenarios with LLM."
    )

    group = parser.add_argument_group("pathes")

    group.add_argument(
        "--data-dir",
        type=str,
        required=True,
        help="Root directory of the evaluated dataset",
    )

    group.add_argument(
        "--report-path",
        type=str,
        required=False,
        help="Path to save the grading report",
        default=None,
    )

    group = parser.add_argument_group("scenarios")

    exclusive_group = group.add_mutually_exclusive_group(required=True)

    exclusive_group.add_argument(
        "--scenarios",
        type=int,
        help="Number of scenarios to evaluate",
    )

    exclusive_group.add_argument(
        "--scenario-ranges",
        type=str,
        help="Range(s) of scenarios to evaluate. Sample: 1,3,5-10",
    )

    args = parser.parse_args()

    scenarios = list()

    if args.scenarios:
        scenarios = list(range(1, args.scenarios + 1))
    else:
        scenarios = parse_scenarios_ranges(args.scenario_ranges)

    try:
        data_dir = validate_data_path(args.data_dir)
        if args.report_path:
            report_path = validate_report_path(args.report_path)
        else:
            report_path = os.path.join(data_dir, "grades.csv")

    except (ValueError, FileNotFoundError, FileExistsError) as e:
        logger.error("Error: %s", e)
        return 1

    gpt_4_omni = get_gpt4_model()
    o1_mini = get_o1_mini_model()

    grading_report = []

    for filename in os.listdir(data_dir):
        if is_valid_scenario(filename, data_dir, scenarios):
            scenario_id = filename
            (accuracy, completeness) = evaluate_scenario(
                base_path=data_dir,
                scenario_id=scenario_id,
                evaluation_model=o1_mini,
                grading_model=gpt_4_omni
            )

            grading_report.append(accuracy.to_data_frame("accuracy"))
            grading_report.append(completeness.to_data_frame("completeness"))

            scenarios.remove(int(scenario_id))

    save_grading_report(report_path, grading_report)

    if len(scenarios) > 0:
        logger.warning("Missed scenario(s): %s", scenarios)


if __name__ == "__main__":
    main()
