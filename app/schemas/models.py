from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


WorkflowStatus = Literal["success", "failed", "needs_input"]


class AgentStepResult(BaseModel):
    status: WorkflowStatus
    summary: str
    artifacts: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    next_action: str = "continue"


class RequirementAnalysis(AgentStepResult):
    functional_requirements: list[str] = Field(default_factory=list)
    non_functional_requirements: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class Plan(AgentStepResult):
    implementation_steps: list[str] = Field(default_factory=list)
    affected_paths: list[str] = Field(default_factory=list)
    test_strategy: list[str] = Field(default_factory=list)
    rollback_strategy: list[str] = Field(default_factory=list)
    requires_human_confirmation: bool = False


class CodeResult(AgentStepResult):
    changed_files: list[str] = Field(default_factory=list)
    implementation_notes: list[str] = Field(default_factory=list)


class TestResult(AgentStepResult):
    command: str
    passed: bool = False
    stdout_tail: str = ""
    stderr_tail: str = ""
    fix_suggestions: list[str] = Field(default_factory=list)


class DeployResult(AgentStepResult):
    command: str
    deployed: bool = False
    service_url: str | None = None
    health_check: str = ""
    rollback_suggestion: str = ""


class FinalWorkflowReport(BaseModel):
    workflow_id: str
    status: WorkflowStatus
    user_request: str
    requirement_analysis: RequirementAnalysis | None = None
    plan: Plan | None = None
    code_result: CodeResult | None = None
    test_result: TestResult | None = None
    deploy_result: DeployResult | None = None
    retries_used: int = 0
    summary: str
