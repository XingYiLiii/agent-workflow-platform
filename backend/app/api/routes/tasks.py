import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.task import Task
from app.models.workflow_run import WorkflowRun
from app.schemas.task import TaskCreate, TaskListRead, TaskRead
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


@router.post("/{task_id}/run", status_code=status.HTTP_201_CREATED)
def run_task(task_id: uuid.UUID, db: Session = Depends(get_db)) -> dict[str, object]:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return _workflow_run_response(run_task_workflow(task, db))


@router.get("/{task_id}/workflow")
def get_task_workflow(task_id: uuid.UUID, db: Session = Depends(get_db)) -> dict[str, object]:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    statement = (
        select(WorkflowRun)
        .where(WorkflowRun.task_id == task_id)
        .order_by(WorkflowRun.created_at.desc())
    )
    workflow_run = db.scalar(statement)
    if workflow_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found")
    return _workflow_run_response(workflow_run)


def _workflow_run_response(workflow_run: WorkflowRun) -> dict[str, object]:
    return {
        "id": str(workflow_run.id),
        "task_id": str(workflow_run.task_id),
        "status": workflow_run.status,
        "current_node": workflow_run.current_node,
        "node_history": workflow_run.node_history,
        "result": workflow_run.result,
    }
