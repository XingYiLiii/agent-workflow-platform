import uuid

from pydantic import BaseModel, Field


class ExecutionStep(BaseModel):
    id: str = Field(min_length=1)
    description: str = Field(min_length=1)


class ExecutionPlan(BaseModel):
    goal: str = Field(min_length=1)
    steps: list[ExecutionStep] = Field(min_length=1)


class StepResult(BaseModel):
    step_id: str
    status: str
    result: str


class ReviewResult(BaseModel):
    passed: bool
    issues: list[str] = Field(default_factory=list)


class FinalOutput(BaseModel):
    content: str


class WorkflowState(BaseModel):
    task_id: uuid.UUID
    goal: str = Field(min_length=1)
    plan: ExecutionPlan | None = None
    current_step: int = 0
    step_results: list[StepResult] = Field(default_factory=list)
    review_result: ReviewResult | None = None
    final_output: FinalOutput | None = None
    error: str | None = None
