# Anterion Agent - Microservice

## About

This repo accepts requests from the SWE-agent and sends them to the
frontend, for the appropriate user.

## Usage

### `.env`

Create a `.env` file in this repo and fill it with the following details:

```bash
OPENAI_API_KEY=<OPENAI_API_KEY_GOES_HERE>
ANTHROPIC_API_KEY=<ANTHROPIC_API_KEY_GOES_HERE>
SWE_AGENT_PATH=<PATH_TO_THE_SWE_AGENT_DIRECTORY>
PYTHON_PATH=<PATH_TO_SWE_AGENT_CONDA_ENV_PYTHON_BIN>

DOCKER_HOST_VOLUME_PATH=<PATH_TO_DOCKER_VOLUME_DIRECTORY>
DOCKER_CONTAINER_VOLUME_PATH=/usr/app

SWE_AGENT_PER_INSTANCE_COST_LIMIT=<MAXIMUM_AMOUNT_OF_USD_TO_SPEND_PER_TASK>
SWE_AGENT_TIMEOUT=25
SWE_AGENT_MODEL_NAME=<FILL_THIS_IN_WITH_DESIRED_MODEL_NAME>
```

#### Full List of Models

OpenAI Models:
- gpt3
- gpt3-legacy
- gpt4 (NOTE: This is the default model)
- gpt4-legacy
- gpt4-0125
- gpt3-0125

Anthropic Models:
- claude (NOTE: This is Claude 2.0)
- claude-opus
- claude-sonnet
- claude-haiku

## Installation

Firstly, you will need the `SWE-agent` conda env setup before using this submodule.
Once you have done that, activate the environment by doing the following:

```bash
conda activate swe-agent
```

Then install the requirements for this submodule using:

```bash
pip install -r requirements.txt
```

Then run the program using the following command:

```bash
python -m uvicorn app:app --port 3000 --reload
```