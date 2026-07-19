from fastapi.testclient import TestClient


def test_task_details_aggregates_execution_records(client: TestClient) -> None:
    create_response = client.post(
        "/tasks", json={"title": "Calculate discount", "input": "calculate: 100*0.8"}
    )
    task_id = create_response.json()["id"]

    run_response = client.post(f"/tasks/{task_id}/run")
    assert run_response.status_code == 201

    details_response = client.get(f"/tasks/{task_id}/details")

    assert details_response.status_code == 200
    details = details_response.json()
    assert details["task"]["id"] == task_id
    assert details["workflow"]["node_history"] == ["planner", "executor", "reviewer", "finalizer"]
    assert details["tool_calls"][0]["tool_name"] == "calculator"
    assert details["checkpoints"][-1]["current_node"] == "finalizer"
    assert details["final_output"]["content"]


def test_dashboard_page_is_available(client: TestClient) -> None:
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "Agent Workflow Platform" in response.text
    assert "/tasks/" in response.text
