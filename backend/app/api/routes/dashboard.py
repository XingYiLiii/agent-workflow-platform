# ruff: noqa: E501
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def dashboard() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Agent Workflow Platform</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, system-ui, sans-serif; }
    body { max-width: 1120px; margin: 0 auto; padding: 2rem; background: #10151f; color: #e8edf7; }
    h1 { margin-bottom: .25rem; } .muted { color: #9aa8bf; }
    main { display: grid; grid-template-columns: 300px 1fr; gap: 1.25rem; margin-top: 1.5rem; }
    section { background: #182131; border: 1px solid #2b3a52; border-radius: 12px; padding: 1rem; }
    button { width: 100%; margin: .4rem 0; text-align: left; padding: .7rem; border-radius: 8px; border: 1px solid #34445e; background: #202c40; color: inherit; cursor: pointer; }
    button:hover { background: #293a55; } .status { color: #68d391; font-weight: 700; }
    .flow { display: flex; flex-wrap: wrap; gap: .5rem; margin: .75rem 0; } .node { padding: .35rem .6rem; border-radius: 999px; background: #264166; }
    pre { overflow: auto; white-space: pre-wrap; background: #0d131d; padding: .8rem; border-radius: 8px; }
    .empty { padding: 2rem 0; color: #9aa8bf; } @media (max-width: 760px) { main { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <h1>Agent Workflow Platform</h1>
  <p class="muted">Inspectable task execution: workflow nodes, tool traces, checkpoints, and final output.</p>
  <main>
    <section><h2>Tasks</h2><div id="tasks" class="empty">Loading tasks...</div></section>
    <section><h2 id="detail-title">Execution detail</h2><div id="detail" class="empty">Select a task to inspect its execution.</div></section>
  </main>
  <script>
    const pretty = (value) => JSON.stringify(value, null, 2);
    const panel = document.getElementById('detail');
    async function loadDetails(id) {
      const response = await fetch(`/tasks/${id}/details`);
      const data = await response.json();
      document.getElementById('detail-title').textContent = data.task.title;
      const nodes = data.workflow?.node_history || [];
      panel.innerHTML = `
        <p><span class="status">${data.task.status}</span> | retries: ${data.task.retry_count}</p>
        <p>${data.task.input}</p>
        <h3>Workflow</h3><div class="flow">${nodes.map(node => `<span class="node">${node}</span>`).join(' -> ') || 'Not started'}</div>
        <h3>Tool calls</h3><pre>${pretty(data.tool_calls)}</pre>
        <h3>Checkpoints</h3><pre>${pretty(data.checkpoints.map(({state_snapshot, ...item}) => item))}</pre>
        <h3>Final output</h3><pre>${pretty(data.final_output)}</pre>`;
    }
    async function loadTasks() {
      const response = await fetch('/tasks');
      const data = await response.json();
      const tasks = document.getElementById('tasks');
      if (!data.items.length) { tasks.textContent = 'No tasks yet. Create one through POST /tasks.'; return; }
      tasks.innerHTML = '';
      data.items.forEach(task => {
        const button = document.createElement('button');
        button.textContent = `${task.title} - ${task.status}`;
        button.onclick = () => loadDetails(task.id);
        tasks.appendChild(button);
      });
      loadDetails(data.items[0].id);
    }
    loadTasks().catch(error => { document.getElementById('tasks').textContent = error.message; });
  </script>
</body>
</html>"""
