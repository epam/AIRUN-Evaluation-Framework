# auto_llm_eval Package

This package provides functionality for evaluating and analyzing LLM (Large Language Model) responses based on predefined criteria.

## EvaluationReport Class

The `EvaluationReport` class is designed to parse, analyze, and format evaluation reports generated from LLM testing sessions. It processes raw text reports and extracts relevant metrics and insights.

### Installation

```bash
pip install auto-llm-eval
```

### Usage

```python
from epam.auto_llm_eval import EvaluationReport

# Create a report from raw text
report_text = """
- **Pass** (95%): Response follows the correct format
  The response is well-structured and follows all formatting requirements.

- **Fail** (60%): Contains all required information
  Missing some key details in the response.

---
Total steps evaluated: 2
Number of passed steps: 1
Number of failed steps: 1
"""

report = EvaluationReport(report_text)

# Access report metrics
total_steps = report.get_total_steps()      # Returns 2
passed_steps = report.get_passed_steps()    # Returns 1
failed_steps = report.get_failed_steps()    # Returns 1
pass_rate = report.get_pass_rate()          # Returns 0.5 (50%)

# Get all evaluation steps
steps = report.get_steps()  # Returns List[EvaluationStep]

# Access individual step information
for step in steps:
    print(f"Step: {step.name}")
    print(f"Status: {step.status}")
    print(f"Confidence: {step.confidence}%")
    if step.reasoning:
        print(f"Reasoning: {step.reasoning}")
```

### Key Features

- Parse raw evaluation reports into structured data
- Extract evaluation steps with status, confidence, and reasoning
- Calculate metrics like total steps, passed/failed counts, and pass rate
- Access both summary statistics and detailed step information

### Data Classes

#### EvaluationStep

Represents a single evaluation step with the following attributes:
- `status` (str): Status of the step ('Pass' or 'Fail')
- `confidence` (float): Confidence percentage (0-100)
- `name` (str): Name/description of the step
- `reasoning` (Optional[str]): Optional reasoning for status and confidence

#### EvaluationReport

Main class for handling evaluation reports with the following methods:
- `get_text()`: Get the original report text
- `get_total_steps()`: Get total number of evaluation steps
- `get_passed_steps()`: Get number of passed steps
- `get_failed_steps()`: Get number of failed steps
- `get_pass_rate()`: Get the pass rate as a float (0-1)
- `get_steps()`: Get list of all evaluation steps

### Report Format

The report text should follow this format:
```
- **Pass/Fail** (confidence%): Step name
  Optional reasoning text

---
Total steps evaluated: X
Number of passed steps: Y
Number of failed steps: Z
``` 