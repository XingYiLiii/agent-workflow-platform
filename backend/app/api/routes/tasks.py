import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.task import Task, TaskStep
from app.models.tool_call import ToolCall
from app.models.workflow_checkpoint import WorkflowCheckpoint
from app.models.workflow_run import WorkflowRun
from app.schemas.task import TaskCreate, TaskListRead, TaskRead
from app.services.workflow_recovery_service import WorkflowRecoveryService
from app.services.workflow_service import run_task_workflow

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)) -> Task:
    task = Task(title=payload.title, input_text=payload.input)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("", response_model=TaskListRead)
def list_tasks(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> TaskListRead:
    statement = select(Task).options(selectinload(Task.steps)).order_by(Task.created_at.desc())
    tasks = list(db.scalars(statement.offset(offset).limit(limit)))
    total = db.scalar(select(func.count()).select_from(Task)) or 0
    return TaskListRead(items=tasks, total=total)


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: uuid.UUID, db: Session = Depends(get_db)) -> Task:
    statement = select(Task).options(selectinload(Task.steps)).where(Task.id == task_id)
    task = db.scalar(statement)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.get("/{task_id}/details")
def get_task_details(task_id: uuid.UUID, db: Session = Depends(get_db)) -> dict[str, object]:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    workflow_run = db.scalar(
        select(WorkflowRun)
        .where(WorkflowRun.task_id == task_id)
        .order_by(WorkflowRun.created_at.desc())
    )
    steps = list(
        db.scalars(select(TaskStep).where(TaskStep.task_id == task_id).order_by(TaskStep.id))
    )
    tool_calls = list(
        db.scalars(
            select(ToolCall).where(ToolCall.task_id == task_id).order_by(ToolCall.created_at)
        )
    )
    checkpoints = list(
        db.scalars(
            select(WorkflowCheckpoint)
            .where(WorkflowCheckpoint.task_id == task_id)
            .order_by(WorkflowCheckpoint.created_at)
        )
    )
    workflow = _workflow_run_response(workflow_run) if workflow_run else None
    return {
        "task": _task_detail_response(task),
        "workflow": workflow,
        "steps": [_step_response(step) for step in steps],
        "tool_calls": [_tool_call_response(tool_call) for tool_call in tool_calls],
        "checkpoints": [_checkpoint_response(checkpoint) for checkpoint in checkpoints],
        "final_output": workflow_run.result.get("final_output")
        if workflow_run and workflow_run.result
        else None,
    }


@router.post("/{task_id}/run", status_code=status.HTTP_201_CREATED)
def run_task(task_id: uuid.UUID, db: Session = Depends(get_db)) -> dict[str, object]:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return _workflow_run_response(run_task_workflow(task, db))


@router.post("/{task_id}/retry")
def retry_task(task_id: uuid.UUID, db: Session = Depends(get_db)) -> dict[str, object]:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.status != "failed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Only failed tasks can be retried"
        )
    if task.retry_count >= task.max_retry:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Task retry limit reached")
    task.retry_count += 1
    db.commit()
    try:
        workflow_run = WorkflowRecoveryService().recover(task, db)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    return _workflow_run_response(workflow_run)


@router.get("/{task_id}/workflow")
def get_task_workflow(task_id: uuid.UUID, db: Session = Depends(get_db)) -> dict[str, object]:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    workflow_run = db.scalar(
        select(WorkflowRun)
        .where(WorkflowRun.task_id == task_id)
        .order_by(WorkflowRun.created_at.desc())
    )
    if workflow_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found")
    return _workflow_run_response(workflow_run)


def _task_detail_response(task: Task) -> dict[str, object]:
    return {
        "id": str(task.id),
        "title": task.title,
        "input": task.input_text,
        "status": task.status,
        "retry_count": task.retry_count,
        "error_type": task.error_type,
        "error_message": task.error_message,
        "failed_node": task.failed_node,
        "failed_at": task.failed_at,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }


def _step_response(step: TaskStep) -> dict[str, object]:
    return {"id": str(step.id), "name": step.name, "status": step.status, "result": step.result}


def _tool_call_response(tool_call: ToolCall) -> dict[str, object]:
    return {
        "id": str(tool_call.id),
        "tool_name": tool_call.tool_name,
        "input": tool_call.input,
        "output": tool_call.output,
        "status": tool_call.status,
        "error_message": tool_call.error_message,
        "created_at": tool_call.created_at,
    }


def _checkpoint_response(checkpoint: WorkflowCheckpoint) -> dict[str, object]:
    return {
        "id": str(checkpoint.id),
        "workflow_run_id": str(checkpoint.workflow_run_id),
        "current_node": checkpoint.current_node,
        "state_snapshot": checkpoint.state_snapshot,
        "created_at": checkpoint.created_at,
    }


def _workflow_run_response(workflow_run: WorkflowRun) -> dict[str, object]:
    return {
        "id": str(workflow_run.id),
        "task_id": str(workflow_run.task_id),
        "status": workflow_run.status,
        "current_node": workflow_run.current_node,
        "node_history": workflow_run.node_history,
        "result": workflow_run.result,
    }
