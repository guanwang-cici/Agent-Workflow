# OpenAI Agents SDK + Langfuse Five-Agent Workflow

This project implements a local five-agent delivery workflow:

```text
requirement analyst -> planner -> coder -> tester -> deployer
```

The workflow uses the OpenAI Agents SDK for agent execution and Langfuse/OpenTelemetry for observability.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Fill in `OPENAI_API_KEY` in `.env`.

## Start local Langfuse

```bash
cd docker/langfuse
docker compose up -d
```

Open `http://localhost:3000`, create a project, then copy the project keys into `.env`.

## Run the workflow

```bash
agent-workflow "Add a multiply function to the demo project and test it"
```

The workflow prints a structured JSON report and flushes Langfuse spans before exit.

## Safety model

Local command execution is allowlisted through `WORKFLOW_ALLOWED_COMMANDS`. File writes are restricted to `WORKSPACE_PATH` through the coder agent's workspace tools.

## Development checks

```bash
pytest
```
