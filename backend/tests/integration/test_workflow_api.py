from fastapi.testclient import TestClient


def test_run_and_read_task_workflow(client: TestClient) -> None:
    create_response = client.post(
        "/tasks", json={"title": "Analyze sales", "input": "Analyze the uploaded CSV"}
    )
    task_id = create_response.json()["id"]

    run_response = client.post(f"/tasks/{task_id}/run")

    assert run_response.status_code == 201
    workflow = run_response.json()
    assert workflow["status"] == "success"
    assert workflow["node_history"] == ["planner", "executor", "reviewer", "finalizer"]
    assert workflow["result"]["final_output"]["content"]

    read_response = client.get(f"/tasks/{task_id}/workflow")
    assert read_response.status_code == 200
    assert read_response.json()["id"] == workflow["id"]
