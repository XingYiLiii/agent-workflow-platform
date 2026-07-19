from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.task import Task, TaskStep


def test_task_persists_its_steps() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        task = Task(title="Analyze sales", input_text="Analyze the uploaded CSV")
        task.steps.append(TaskStep(name="Plan analysis"))
        session.add(task)
        session.commit()

        saved_task = session.scalar(select(Task))

        assert saved_task is not None
        assert saved_task.status == "pending"
        assert saved_task.steps[0].name == "Plan analysis"
        assert saved_task.steps[0].status == "pending"
