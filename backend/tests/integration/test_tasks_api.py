from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import create_app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    app = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_create_list_and_get_task(client: TestClient) -> None:
    create_response = client.post(
        "/tasks",
        json={"title": "Analyze sales", "input": "Analyze the uploaded CSV"},
    )

    assert create_response.status_code == 201
    created_task = create_response.json()
    assert created_task["title"] == "Analyze sales"
    assert created_task["input"] == "Analyze the uploaded CSV"
    assert created_task["status"] == "pending"
    assert created_task["steps"] == []

    list_response = client.get("/tasks")
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1
    assert list_response.json()["items"][0]["id"] == created_task["id"]

    get_response = client.get(f"/tasks/{created_task['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == created_task["id"]


def test_get_missing_task_returns_not_found(client: TestClient) -> None:
    response = client.get("/tasks/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"
