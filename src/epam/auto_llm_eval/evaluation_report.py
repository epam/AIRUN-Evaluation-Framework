"""
Module for handling LLM evaluation reports.

This module provides functionality to parse, analyze and format evaluation
reports generated from LLM testing sessions. It processes raw text reports and
extracts relevant metrics and insights.
"""
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class EvaluationStep:
    """
    Represents a single evaluation step with its status, confidence, name and
    reasoning.

    Attributes:
        status (str): Status of the step ('Pass' or 'Fail')
        confidence (float): Confidence percentage (0-100)
        name (str): Name/description of the step
        reasoning (Optional[str]): Optional reasoning for status and confidence
        weight (float): Weight of the step
    """
    status: str
    confidence: float
    name: str
    reasoning: Optional[str] = None
    weight: Optional[float] = 1.0

    @classmethod
    def from_text(
        cls, text: str, weight: Optional[float] = 1.0
    ) -> Optional['EvaluationStep']:
        """
        Parse a step from its full text representation (header + reasoning).

        Args:
            text (str): Full step text including header and reasoning

        Returns:
            Optional[EvaluationStep]: Parsed step or None if text is invalid
        """
        lines = text.strip().split('\n')
        if not lines:
            return None

        # Parse header
        pattern = r'- \*\*(Pass|Fail)\*\* \((\d+)%\): (.+)'
        match = re.match(pattern, lines[0])
        if not match:
            return None

        status, confidence, name = match.groups()
        reasoning = '\n'.join(lines[1:]).strip() or None

        return cls(
            status=status,
            confidence=float(confidence),
            name=name.strip(),
            reasoning=reasoning,
            weight=weight
        )


class EvaluationReport:
    """
    A class to handle and process LLM evaluation reports.

    This class takes raw evaluation reports in text format and provides methods
    to analyze results, extract metrics, and generate formatted outputs.

    Attributes:
        text (str): The original raw report text
        steps (List[EvaluationStep]): List of evaluation steps
        total_steps (int): Total number of steps evaluated
        passed_steps (int): Number of passed steps
        failed_steps (int): Number of failed steps
    """

    SUMMARY_SEPARATOR = "---"
    SUMMARY_MARKERS = {
        "total": "Total steps evaluated:",
        "passed": "Number of passed steps:",
        "failed": "Number of failed steps:"
    }
    STEP_MARKER = "- **"

    def __init__(self, report_text: str,
                 evaluation_steps: Optional[List[EvaluationStep]] = None
                 ):
        """
        Initialize an EvaluationReport instance.

        Args:
            report_text (str): Raw evaluation report text to be processed
        """
        self.text = report_text
        self.steps: List[EvaluationStep] = []
        self.total_steps = None
        self.passed_steps = None
        self.failed_steps = None

        # First parse the report to populate steps
        self._parse_report(report_text)

        # Then enrich with weights if external steps provided
        if evaluation_steps:
            self._enrich_with_weights(evaluation_steps)

    def _find_matching_step(
        self, step_name: str, evaluation_steps: List[EvaluationStep]
    ) -> Optional[EvaluationStep]:
        """
        Find a matching evaluation step by name from a list of steps.

        Performs case-insensitive comparison of stripped step names to find
        matches.

        Args:
            step_name (str): Name of the step to find
            evaluation_steps (List[EvaluationStep]): List of steps to search
            through

        Returns:
            Optional[EvaluationStep]: Matching step if found, None otherwise
        """
        for step in evaluation_steps:
            if step.name.lower().strip() == step_name.lower().strip():
                return step
        return None

    def _enrich_with_weights(
        self, evaluation_steps: List[EvaluationStep]
    ) -> None:
        """
        Update steps with weights from metadata.

        Args:
            evaluation_steps: List of predefined steps with weights
        """
        for step in self.steps:
            matching_step = self._find_matching_step(
                step.name, evaluation_steps
            )
            step.weight = matching_step.weight if matching_step else 1.0

    def _parse_summary(self, line: str) -> None:
        """Parse a summary line to extract metrics."""
        if line.startswith('Total steps evaluated:'):
            self.total_steps = int(line.split(': ')[1])
        elif line.startswith('Number of passed steps:'):
            self.passed_steps = int(line.split(': ')[1])
        elif line.startswith('Number of failed steps:'):
            self.failed_steps = int(line.split(': ')[1])

    def _split_report_sections(self, report_text: str) -> Tuple[str, str]:
        """Split the report into main content and summary sections."""
        sections = report_text.split(self.SUMMARY_SEPARATOR)
        if len(sections) != 2:
            raise ValueError(
                "Report must contain steps and summary separated by '---'"
            )
        return sections

    def _parse_report(self, report_text: str) -> None:
        """
        Parse the raw report text to extract metrics and steps.
        """
        main_content, summary = self._split_report_sections(report_text)

        self.steps = self._parse_evaluation_steps(main_content)
        self._parse_summary_section(summary.strip())

    def _parse_evaluation_steps(self, content: str) -> List[EvaluationStep]:
        """
        Parse evaluation steps from the main content.

        Args:
            content (str): Text containing evaluation steps

        Returns:
            List[EvaluationStep]: List of parsed evaluation steps
        """
        steps = []
        current_step_lines = []

        for line in content.split('\n'):
            if line.startswith(self.STEP_MARKER):
                # Process previous step if exists
                if current_step_lines:
                    step = EvaluationStep.from_text(
                        '\n'.join(current_step_lines)
                        )
                    if step:
                        steps.append(step)
                # Start new step
                current_step_lines = [line]
            elif line.strip():
                current_step_lines.append(line)

        # Handle last step
        if current_step_lines:
            step = EvaluationStep.from_text('\n'.join(current_step_lines))
            if step:
                steps.append(step)

        return steps

    def _parse_summary_section(self, summary: str) -> None:
        """Parse the summary section of the report."""
        for line in summary.strip().split('\n'):
            line = line.strip()
            if line.startswith(self.SUMMARY_MARKERS["total"]):
                self.total_steps = int(line.split(': ')[1])
            elif line.startswith(self.SUMMARY_MARKERS["passed"]):
                self.passed_steps = int(line.split(': ')[1])
            elif line.startswith(self.SUMMARY_MARKERS["failed"]):
                self.failed_steps = int(line.split(': ')[1])

    def get_text(self) -> str:
        """Get the original raw report text."""
        return self.text

    def get_total_steps(self) -> int:
        """Get the total number of steps evaluated."""
        return self.total_steps

    def get_passed_steps(self) -> int:
        """Get the number of passed steps."""
        return self.passed_steps

    def get_failed_steps(self) -> int:
        """Get the number of failed steps."""
        return self.failed_steps

    def get_pass_rate(self) -> float:
        """Get the pass rate as a fraction of passed steps over total steps."""
        return self.passed_steps / self.total_steps

    def get_steps(self) -> List[EvaluationStep]:
        """Get the list of evaluation steps."""
        return self.steps

    def get_weighted_score(self) -> float:
        """
        Calculate weighted score based on passed steps and their weights.

        Returns:
            float: Weighted score between 0 and 1, where:
                0 means all steps failed
                1 means all steps passed
        """
        if not self.steps:
            return 0.0

        total_weight = sum(step.weight for step in self.steps)
        if total_weight == 0:
            return 0.0

        weighted_passes = sum(
            step.weight for step in self.steps
            if step.status.lower() == 'pass'
        )

        return weighted_passes / total_weight
