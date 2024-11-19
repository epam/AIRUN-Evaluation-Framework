# Contributing to Auto LLM Eval

Thank you for your interest in contributing to Auto LLM Eval! We welcome
contributions from the community to help improve and grow this automated LLM
evaluation framework.

## Getting Started

- Fork the repository on GitHub
- Clone your forked repository to your local machine
- Set up the Conda environment:
  1. Install Miniconda or Anaconda if you haven't already
  2. Create a new Conda environment from the environment.yml file:
     ```
     conda env create -f environment.yml
     ```
  3. Activate the environment:
     ```
     conda activate auto_llm_eval
     ```

## How to Contribute

1. Check the issue tracker for open issues or create a new one to discuss your idea.
2. Once approved, create a branch for your contribution.
3. Make your changes, following our style guidelines.
4. Write or update tests as necessary.
5. Ensure all tests pass.
6. Submit a pull request.

## Submitting a Pull Request

1. Push your changes to your forked repository.
2. Navigate to the original repository and create a pull request.
3. Provide a clear description of the changes and their purpose.
4. Wait for a maintainer to review your pull request.

## Reporting Bugs

- Use the GitHub issue tracker to report bugs.
- Describe the bug in detail, including steps to reproduce.
- Include any relevant code snippets or error messages.

## Suggesting Enhancements

- Use the GitHub issue tracker to suggest enhancements.
- Clearly describe the enhancement and its potential benefits.
- Be open to discussion and feedback from maintainers and other contributors.

## Style Guidelines

- Follow PEP 8 style guide for Python code.
- Use clear, descriptive variable and function names.
- Write docstrings for all functions and classes.
- Maintain consistent indentation (use spaces, not tabs).
- Ensure compatibility with Python 3.12.
- Run Flake8 linter and Black formatter before submitting your code:
  1. Install Black and Flake8 in your Conda environment:
     ```
     pip install black flake8
     ```
  2. Run Flake8:
     ```
     flake8 .
     ```
  3. Run the Black formatter:
     ```
     black .
     ```
- Address any issues raised by Flake8 and ensure your code conforms to the Black
  formatting style.

## License

By contributing to Auto LLM Eval, you agree that your contributions will be
licensed under the project's license.

---

This document is subject to change. Contributors are encouraged to check for
updates regularly.

EPAM | 2024