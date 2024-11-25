"""
Test the EvaluationReport class.
"""
# pylint: disable=line-too-long
# flake8: noqa: E501

import pytest
from epam.auto_llm_eval.evaluation_report import EvaluationReport, EvaluationStep


@pytest.fixture(name="sample_report")
def fixture_sample_report():
    """
    Sample evaluation report text.
    """
    return """# Evaluation Report

- **Pass** (100%): Verify the function code is written in Python
- **Pass** (100%): Verify the function has a docstring
- **Fail** (100%): Verify the function has type hints

    The function `sum_integers` in the provided code does not include type
    hints. We can conclude this by observing the function definition:

    ```python
    def sum_integers(a, b):
    ```

    In Python, type hints are typically added after the parameter names and
    before the colon, followed by the return type hint after the `->` symbol.
    The correct format with type hints would look like this:

    ```python
    def sum_integers(a: int, b: int) -> int:
    ```

    The absence of `: int` after the parameters `a` and `b`, and the missing
    `-> int` before the colon at the end of the function definition, clearly
    indicates that type hints are not present in the given function.

- **Pass** (90%): Ensure the code is elegant

    The provided function is simple and straightforward, adhering to Python's
    clean and readable syntax. However, incorporating type hints could enhance
    clarity and maintainability, making the code more explicit about the
    expected input and output types.

---

Total steps evaluated: 4
Number of passed steps: 3
Number of failed steps: 1"""


@pytest.fixture(name="sample_completeness_report")
def fixture_sample_completeness_report():
    """
    Sample completeness evaluation report text.
    """
    return """# Evaluation Report

- **Pass** (100%): Confirm the component includes a search feature in the dropdown
- **Pass** (100%): Check that the component is navigable via keyboard
- **Pass** (100%): Verify items in the dropdown can be selected by pressing the Enter key
- **Pass** (100%): Confirm the dropdown list opens when Enter is pressed
- **Pass** (90%): Ensure the focus returns to the select component after the dropdown is closed

    The component is designed to be focusable with `tabIndex={0}` and handles keyboard events to manage focus. While there is no explicit code to return focus to the select component after the dropdown is closed, it is likely that the focus remains on the main div due to its focusable nature. However, without explicit focus management, there is a slight uncertainty regarding the exact behavior.

- **Pass** (100%): Verify the dropdown closes upon selecting an item via keyboard
- **Pass** (100%): Verify the dropdown closes upon selecting an item via mouse
- **Pass** (100%): Confirm the dropdown closes when the Escape key is pressed
- **Pass** (100%): Ensure the dropdown closes when clicking outside the component

---

Total steps evaluated: 9  
Number of passed steps: 9  
Number of failed steps: 0"""


@pytest.fixture(name="sample_accuracy_report")
def fixture_sample_accuracy_report():
    """
    Sample accuracy report text.
    """
    return """# Evaluation Report

- **Pass** (100%): Ensure the application does not contain unused imports or code
- **Pass** (100%): Ensure the codebase is structured and follows TypeScript and React best practices (state, hooks, effects)
- **Pass** (100%): Ensure the application is free of memory leaks and unnecessary re-renders
- **Pass** (90%): Ensure the application is compatible with the latest version of React and TypeScript

    The project is initialized using `create-react-app` with the TypeScript template, which typically ensures compatibility with recent versions. However, the specific versions of React and TypeScript are not explicitly mentioned, so absolute compatibility cannot be confirmed.

- **Pass** (90%): Ensure the application is free of console errors and warnings

    The provided code does not contain any obvious errors or issues that would generate console warnings. However, without running the application, it's not possible to guarantee that no console errors or warnings will appear during execution.

- **Pass** (100%): Ensure app does not access DOM elements to retrieve the values of text fields
- **Pass** (100%): Ensure app does not directly manipulate the DOM outside of React’s virtual DOM
- **Pass** (100%): Ensure app does not overuse refs for DOM access instead of React’s state and props
- **Pass** (100%): Ensure app does not have too many re-renders due to state or prop changes
- **Pass** (80%): Ensure the code is decomposed to the set of the components with using single responsibility

    The application consists of a single `App` component. While this is sufficient for a simple application, decomposing the code into smaller, more focused components could enhance maintainability and adhere more closely to the single responsibility principle.

- **Pass** (100%): Ensure the code does not contain any duplicates and follow DRY principles
- **Fail** (0%): App has the same DOM tree structure and classes as in the original application.

    The original application's DOM tree structure and classes are not provided, so it's impossible to verify if they match.

- **Pass** (100%): App does correctly use useEffect, avoiding infinite loops
- **Pass** (90%): Confirm that axios is installed and listed as a dependency in package.json

    The installation command for `axios` is provided (`npm install axios`), which should add it to `package.json`. However, the actual `package.json` file is not shown to confirm its inclusion.

- **Pass** (100%): Verify that the fetched data is stored in a state variable using the useState hook
- **Pass** (100%): Verify that the code is optimized and does not contain any unnecessary parts or TODOs
- **Pass** (90%): Ensure that TypeScript is correctly integrated and used throughout the codebase

    TypeScript is appropriately used in the provided `App.tsx` file, including the definition of interfaces. However, without access to the entire codebase, it's not possible to confirm that TypeScript is consistently integrated across all parts of the application.

- **Fail** (0%): Verify that React.StrictMode is used in index.tsx.

    The `index.tsx` file is not provided, so it's not possible to verify whether `React.StrictMode` is used.

---

Total steps evaluated: 18  
Number of passed steps: 15  
Number of failed steps: 3"""


@pytest.fixture(name="weighted_steps")
def fixture_weighted_steps():
    """
    Sample evaluation steps with custom weights.
    """
    return [
        EvaluationStep("Pass", 100, "Verify the function code is written in Python", weight=1.0),
        EvaluationStep("Pass", 100, "Verify the function has a docstring", weight=2.0),
        EvaluationStep("Fail", 100, "Verify the function has type hints", weight=3.0),
        EvaluationStep("Pass", 90, "Ensure the code is elegant", weight=1.0),
    ]


def test_evaluation_report_text(sample_report):
    """
    Test the get_text method of the EvaluationReport class.
    """
    report = EvaluationReport(sample_report)
    retrieved_text = report.get_text()

    assert retrieved_text == sample_report


def test_evaluation_report_metrics(sample_report):
    """
    Test the metrics retrieval methods of the EvaluationReport class.
    """
    report = EvaluationReport(sample_report)

    assert report.get_total_steps() == 4
    assert report.get_passed_steps() == 3
    assert report.get_failed_steps() == 1
    assert report.get_pass_rate() == 0.75  # 3/4 = 75% pass rate


def test_completeness_report_metrics(sample_completeness_report):
    """
    Test the metrics retrieval methods for completeness report.
    """
    report = EvaluationReport(sample_completeness_report)

    assert report.get_total_steps() == 9
    assert report.get_passed_steps() == 9
    assert report.get_failed_steps() == 0
    assert report.get_pass_rate() == 1.0  # 9/9 = 100% pass rate


def test_accuracy_report_metrics(sample_accuracy_report):
    """
    Test the metrics retrieval methods for accuracy report.
    """
    report = EvaluationReport(sample_accuracy_report)

    assert report.get_total_steps() == 18
    assert report.get_passed_steps() == 15
    assert report.get_failed_steps() == 3
    assert report.get_pass_rate() == pytest.approx(0.833, rel=1e-3)  # 15/18 ≈ 83.3% pass rate


def test_evaluation_steps_parsing(sample_report):
    """
    Test the parsing of individual evaluation steps.
    """
    report = EvaluationReport(sample_report)
    steps = report.get_steps()

    assert len(steps) == 4

    # Test step without reasoning
    python_step = next(s for s in steps if s.name == "Verify the function code is written in Python")
    assert isinstance(python_step, EvaluationStep)
    assert python_step.status == "Pass"
    assert python_step.confidence == 100
    assert python_step.reasoning is None

    # Test step with reasoning
    type_hints_step = next(s for s in steps if s.name == "Verify the function has type hints")
    assert type_hints_step.status == "Fail"
    assert type_hints_step.confidence == 100
    assert type_hints_step.reasoning is not None
    assert "The function `sum_integers`" in type_hints_step.reasoning

    # Test another step with reasoning
    elegant_step = next(s for s in steps if s.name == "Ensure the code is elegant")
    assert elegant_step.status == "Pass"
    assert elegant_step.confidence == 90
    assert elegant_step.reasoning is not None
    assert "The provided function is simple" in elegant_step.reasoning


def test_step_parsing():
    """
    Test the EvaluationStep.from_text static method.
    """
    # Test valid step without reasoning
    text = '- **Pass** (100%): Test step name'
    step = EvaluationStep.from_text(text)
    assert step is not None
    assert step.status == "Pass"
    assert step.confidence == 100
    assert step.name == "Test step name"
    assert step.reasoning is None

    # Test valid step with reasoning
    text = '''- **Fail** (90%): Test step with reasoning

    This is the reasoning
    with multiple lines'''
    step = EvaluationStep.from_text(text)
    assert step is not None
    assert step.status == "Fail"
    assert step.confidence == 90
    assert step.name == "Test step with reasoning"
    assert step.reasoning == "This is the reasoning\n    with multiple lines"

    # Test invalid text
    text = 'Invalid line format'
    step = EvaluationStep.from_text(text)
    assert step is None


def test_completeness_report_steps(sample_completeness_report):
    """
    Test the parsing of steps in completeness report.
    """
    report = EvaluationReport(sample_completeness_report)
    steps = report.get_steps()

    assert len(steps) == 9

    # Test step with reasoning
    focus_step = next(step for step in steps if "focus returns" in step.name)
    assert focus_step.status == "Pass"
    assert focus_step.confidence == 90
    assert focus_step.reasoning is not None
    assert "tabIndex={0}" in focus_step.reasoning


def test_accuracy_report_steps(sample_accuracy_report):
    """
    Test the parsing of steps in accuracy report.
    """
    report = EvaluationReport(sample_accuracy_report)
    steps = report.get_steps()

    assert len(steps) == 18

    # Test failed step with 0% confidence
    strict_mode_step = next(step for step in steps if "React.StrictMode" in step.name)
    assert strict_mode_step.status == "Fail"
    assert strict_mode_step.confidence == 0
    assert strict_mode_step.reasoning is not None
    assert "The `index.tsx` file is not provided" in strict_mode_step.reasoning


def test_weighted_score_calculation(sample_report, weighted_steps):
    """
    Test the weighted score calculation with custom step weights.
    """
    report = EvaluationReport(sample_report, weighted_steps)

    # Total weight = 7.0
    # Passed weights = 1.0 + 2.0 + 1.0 = 4.0
    # Expected score = 4.0 / 7.0 ≈ 0.571
    assert report.get_weighted_score() == pytest.approx(0.571, rel=1e-3)


def test_weighted_score_default_weights(sample_report):
    """
    Test the weighted score calculation with default weights (1.0).
    """
    report = EvaluationReport(sample_report)

    # With default weights of 1.0, weighted score should equal pass rate
    assert report.get_weighted_score() == report.get_pass_rate()
