# Automatic LLM evaluation framework

This repository contains a tool for automatically evaluating and grading Large
Language Model (LLM) answers using another LLM as an evaluator. It is part of
AI/RUN <sup>TM</sup> Engineering Benchmark. See more details in [AI/RUN
<sup>TM</sup> Engineering
Benchmarkhttps://github.com/epam/AIRUN-Engineering-Benchmark) to understand the
whole picture on what the benchmark is and what repositories are involved.

## Overview

The Auto LLM Evaluator is designed to assess the quality of LLM-generated
answers based on predefined evaluation criteria. It uses the Azure OpenAI
service to perform the evaluation and grading.

## Key Features

- Evaluates LLM answers for completeness and accuracy
- Grades answers on a scale of 1 to 5
- Generates detailed evaluation reports
- Calculates confidence scores for evaluations
- Saves evaluation results in CSV format

## Setup

### Prerequisites

1. The framework reads Azure OpenAI API key value from environmental variable AZURE_API_KEY. Create the environmental variable to make it available. For instance:

    `export AZURE_API_KEY=...`

### Run Environment Setup

<details>
<summary>MacOS+Brew+Anaconda</summary>

1. Install `miniconda`

    `brew install --cask miniconda`

2. Create an Anaconda environment

    `conda env create`

3. Activate Anaconda environment called `auto_llm_eval`

    `conda activate auto_llm_eval`

</details>

<details>
<summary>Windows/Unix+Python+venv</summary>

1. Install Python 3.12 or above.

2. Create a virtual environment:

    `python -m venv .venv`

3. Activate the created environment:

```bash
# On Windows, run:
.venv\Scripts\activate

# On Unix or MacOS, run:
source .venv/bin/activate
```

4. Install all the necessary packages:

    `pip install -r ./requirements.txt`

</details>

### VS Code

Install Jupyter extension for VS Code

```
    Name: Jupyter
    Id: ms-toolsai.jupyter
    Description: Jupyter notebook support, interactive programming and computing that supports Intellisense, debugging and more.
    Version: 2024.6.0
    Publisher: Microsoft
    VS Marketplace Link: https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter
```

## How to run Prompt Critic

1. Activate Anaconda or Python virtual environment

    `conda activate auto_llm_eval` or `.venv\Scripts\activate` or `source .venv/bin/activate`

2. Open `notebooks/prompt_critic.ipynb` Jupyter notebook in VS Code

3. Select Notebook Kernel/Python Environments in the upper right corner => `auto_llm_eval` or `.venv`

4. Click `Run All` button

After you finish working with Prompt Critic, deactivate Anaconda environment
with `conda deactivate` or `.venv\Scripts\deactivate` or `source .venv/bin/deactivate`.

## How to run LLM Evaluator

1. Activate Anaconda or Python virtual environment

    `conda activate auto_llm_eval` or `.venv\Scripts\activate` or `source .venv/bin/activate`

2. Export Azure OpenAI API key as an environmental variable

    `export AZURE_API_KEY=...`

3. Run LLM Evaluator

    ```sh
    $ python evaluate.py \
        --data-dir data/sample \
        --scenarios 2 \
        --report-path data/sample/grades.csv
    Evaluating scenario 01_generate_base_component
    Grading scenario 01_generate_base_component
    Evaluating scenario 02_generate_react_app
    Grading scenario 02_generate_react_app
    ```

    Definition of the different parameters:


    ```sh
    $ python evaluate.py --help
    usage: evaluate.py [-h] --data-dir DATA_DIR [--report-path REPORT_PATH] (--scenarios SCENARIOS | --scenario-ranges SCENARIO_RANGES)

    Evaluate benchmark scenarios with LLM.

    options:
      -h, --help            show this help message and exit

    pathes:
      --data-dir DATA_DIR   Root directory of the evaluated dataset
      --report-path REPORT_PATH
                            Path to save the grading report

    scenarios:
      --scenarios SCENARIOS
                            Number of scenarios to evaluate
      --scenario-ranges SCENARIO_RANGES
                            Range(s) of scenarios to evaluate. Sample: 1,3,5-10
    ```
    ## 🤝 Contributing

    We appreciate all contributions to improve the AI/RUN <sup>TM</sup> Engineering Benchmark. Please see our [Contribution Guidelines](CONTRIBUTING.md) for more information on how to get involved.

    If you have suggestions for new benchmark scenarios or improvements to existing ones, please open an issue or submit a pull request.

    ## License

    This project is licensed under the [Apache 2.0](/LICENSE).

<p align="center">
    EPAM and EPAM AI/RUN <sup>TM</sup> are trademarks of EPAM Systems, Inc. 
</p>
