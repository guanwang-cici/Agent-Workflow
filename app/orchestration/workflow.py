from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from agents import Runner, trace
from pydantic import BaseModel, Field

from app.agents import (
    build_coder_agent,
    build_deployer_agent,
    build_planner_agent,
    build_requirement_analyst_agent,
    build_tester_agent,
)
from app.observability import flush_langfuse, setup_observability
from app.schemas.models import (
    CodeResult,
    DeployResult,
    FinalWorkflowReport,
    Plan,
    RequirementAnalysis,
    TestResult,
)
from app.tools import build_repo_snapshot, run_allowed_command


class WorkflowConfig(BaseModel):
    workspace_path: Path = Field(default=Path("examples/demo_project"))
    test_command: str = "python -m pytest"
    deploy_command: str = "python app.py --check"
    max_test_retries: int = 2
    environment: str = "local-dev"

    @classmethod
    def from_env(
        cls,
        workspace_path: Path | None = None,
        test_command: str | None = None,
        deploy_command: str | None = None,
    ) -> "WorkflowConfig":
        return cls(
            workspace_path=workspace_path or Path(os.getenv("WORKSPACE_PATH", "examples/demo_project")),
            test_command=test_command or os.getenv("TEST_COMMAND", "python -m pytest"),
            deploy_command=deploy_command or os.getenv("DEPLOY_COMMAND", "python app.py --check"),
            max_test_retries=int(os.getenv("WORKFLOW_MAX_TEST_RETRIES", "2")),
            environment=os.getenv("WORKFLOW_ENVIRONMENT", "local-dev"),
        )


def _coerce_output(value: Any, model_type: type[BaseModel]) -> BaseModel:
    if isinstance(value, model_type):
        return value
    if isinstance(value, str):
        return model_type.model_validate_json(value)
    return model_type.model_validate(value)


async def _run_structured(agent: Any, prompt: str, model_type: type[BaseModel]) -> BaseModel:
    result = await Runner.run(agent, prompt)
    return _coerce_output(result.final_output, model_type)


def _prompt_block(title: str, payload: Any) -> str:
    if isinstance(payload, BaseModel):
        content = payload.model_dump_json(indent=2)
    else:
        content = str(payload)
    return f"{title}\n{content}"


async def run_workflow(user_request: str, config: WorkflowConfig) -> FinalWorkflowReport:
    setup_observability()
    workflow_id = str(uuid.uuid4())
    workspace = config.workspace_path.resolve()

    requirement_analysis: RequirementAnalysis | None = None
    plan: Plan | None = None
    code_result: CodeResult | None = None
    test_result: TestResult | None = None
    deploy_result: DeployResult | None = None
    retries_used = 0

    try:
        with trace(
            "five-agent-delivery-workflow",
            metadata={
                "workflow_id": workflow_id,
                "environment": config.environment,
                "workspace_path": str(workspace),
            },
        ):
            requirement_analysis = await _run_structured(
                build_requirement_analyst_agent(),
                _prompt_block("Analyze this user request:", user_request),
                RequirementAnalysis,
            )
            if requirement_analysis.status != "success":
                return FinalWorkflowReport(
                    workflow_id=workflow_id,
                    status=requirement_analysis.status,
                    user_request=user_request,
                    requirement_analysis=requirement_analysis,
                    summary=requirement_analysis.summary,
                )

            repo_snapshot = build_repo_snapshot(workspace)
            plan_prompt = "\n\n".join(
                [
                    _prompt_block("Requirements:", requirement_analysis),
                    _prompt_block("Repository snapshot:", repo_snapshot),
                ]
            )
            plan = await _run_structured(build_planner_agent(), plan_prompt, Plan)
            if plan.status != "success":
                return FinalWorkflowReport(
                    workflow_id=workflow_id,
                    status=plan.status,
                    user_request=user_request,
                    requirement_analysis=requirement_analysis,
                    plan=plan,
                    summary=plan.summary,
                )

            code_prompt = "\n\n".join(
                [
                    _prompt_block("Plan:", plan),
                    _prompt_block("Repository snapshot:", repo_snapshot),
                    "Return the implementation result. Do not claim files changed unless the change is concrete.",
                ]
            )
            code_result = await _run_structured(build_coder_agent(), code_prompt, CodeResult)

            # Tests are run by deterministic local tooling, then interpreted by the tester agent.
            while True:
                command_result = run_allowed_command(config.test_command, workspace)
                tester_prompt = "\n\n".join(
                    [
                        _prompt_block("Acceptance criteria:", requirement_analysis.acceptance_criteria),
                        _prompt_block("Code result:", code_result),
                        _prompt_block("Test command result:", command_result.model_dump()),
                    ]
                )
                test_result = await _run_structured(build_tester_agent(), tester_prompt, TestResult)
                test_result.passed = command_result.passed
                test_result.command = command_result.command
                test_result.stdout_tail = command_result.stdout
                test_result.stderr_tail = command_result.stderr

                if test_result.passed or retries_used >= config.max_test_retries:
                    break

                retries_used += 1
                revise_prompt = "\n\n".join(
                    [
                        _prompt_block("Previous code result:", code_result),
                        _prompt_block("Test failure:", test_result),
                        "Revise the implementation plan based on this failure.",
                    ]
                )
                code_result = await _run_structured(build_coder_agent(), revise_prompt, CodeResult)

            if not test_result or not test_result.passed:
                return FinalWorkflowReport(
                    workflow_id=workflow_id,
                    status="failed",
                    user_request=user_request,
                    requirement_analysis=requirement_analysis,
                    plan=plan,
                    code_result=code_result,
                    test_result=test_result,
                    retries_used=retries_used,
                    summary="Workflow stopped because tests did not pass.",
                )

            deploy_command_result = run_allowed_command(config.deploy_command, workspace)
            deploy_prompt = "\n\n".join(
                [
                    _prompt_block("Plan:", plan),
                    _prompt_block("Test result:", test_result),
                    _prompt_block("Deploy command result:", deploy_command_result.model_dump()),
                ]
            )
            deploy_result = await _run_structured(build_deployer_agent(), deploy_prompt, DeployResult)
            deploy_result.command = deploy_command_result.command
            deploy_result.deployed = deploy_command_result.passed
            deploy_result.health_check = deploy_command_result.stdout or deploy_command_result.stderr

            return FinalWorkflowReport(
                workflow_id=workflow_id,
                status="success" if deploy_result.deployed else "failed",
                user_request=user_request,
                requirement_analysis=requirement_analysis,
                plan=plan,
                code_result=code_result,
                test_result=test_result,
                deploy_result=deploy_result,
                retries_used=retries_used,
                summary="Workflow completed." if deploy_result.deployed else "Deployment failed.",
            )
    finally:
        flush_langfuse()
