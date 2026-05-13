from __future__ import annotations

import os

from agents import Agent

from app.schemas.models import CodeResult, DeployResult, Plan, RequirementAnalysis, TestResult
from app.tools.file_ops import list_workspace_files, read_workspace_file, write_workspace_file


def _model(agent_model_env: str) -> str:
    return os.getenv(agent_model_env, os.getenv("OPENAI_MODEL", "gpt-4.1"))


def build_requirement_analyst_agent() -> Agent:
    return Agent(
        name="requirement analyst",
        model=_model("REQUIREMENT_ANALYST_MODEL"),
        output_type=RequirementAnalysis,
        instructions=(
            "You convert raw software requests into precise implementation requirements. "
            "Return needs_input if the request is too ambiguous to implement safely. "
            "Keep outputs concise and structured."
        ),
    )


def build_planner_agent() -> Agent:
    return Agent(
        name="planner",
        model=_model("PLANNER_MODEL"),
        output_type=Plan,
        instructions=(
            "You create a conservative engineering plan from approved requirements. "
            "Identify affected files, tests, rollback strategy, and any point that requires "
            "human confirmation. Do not write code."
        ),
    )


def build_coder_agent() -> Agent:
    return Agent(
        name="coder",
        model=_model("CODER_MODEL"),
        output_type=CodeResult,
        tools=[list_workspace_files, read_workspace_file, write_workspace_file],
        instructions=(
            "You implement the planner's task in the provided workspace context. "
            "Use the workspace file tools for concrete changes. Never write outside the workspace. "
            "Return changed_files only for files you actually changed."
        ),
    )


def build_tester_agent() -> Agent:
    return Agent(
        name="tester",
        model=_model("TESTER_MODEL"),
        output_type=TestResult,
        instructions=(
            "You evaluate test output against the acceptance criteria. "
            "If tests fail, summarize the failure and provide focused fix suggestions."
        ),
    )


def build_deployer_agent() -> Agent:
    return Agent(
        name="deployer",
        model=_model("DEPLOYER_MODEL"),
        output_type=DeployResult,
        instructions=(
            "You assess deployment output and decide whether the local deployment or build "
            "completed successfully. Include a rollback suggestion if deployment fails."
        ),
    )
