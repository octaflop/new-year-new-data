import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from anthropic import Anthropic
from fastapi import FastAPI, Request, HTTPException
from fastapi import Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from demos.agenda_demo.managers import TaskManager
from demos.agenda_demo.models import Task

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=TEMPLATE_DIR)

# Initialize TaskManager
task_manager = TaskManager()

# Initialize Anthropic client
anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Default summarization prompt
DEFAULT_PROMPT = """Please analyze these tasks and provide:
1. A high-level summary of the main areas of work
2. Key deadlines and important dates
3. Any potential bottlenecks or overlapping commitments
4. Suggested priority order based on deadlines and dependencies"""


# Store tasks in memory (in a real app, you'd want a database)
class AppState:
    tasks: List[Task] = []
    source_selections: Dict[str, List[Dict[str, str]]] = {}


state = AppState()


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


@app.get("/sources/{importer_name}", response_class=HTMLResponse)
async def get_sources(request: Request, importer_name: str):
    importer = task_manager.importers.get(importer_name)
    if not importer:
        raise HTTPException(status_code=404, detail="Importer not found")

    if not importer.authenticate():
        return templates.TemplateResponse(
            "components/error.html",
            {
                "request": request,
                "message": f"Failed to authenticate with {importer_name}"
            }
        )

    sources = importer.get_available_sources()
    state.source_selections[importer_name] = sources

    return templates.TemplateResponse(
        "components/source_list.html",
        {
            "request": request,
            "sources": sources,
            "importer_name": importer_name
        }
    )


@app.post("/import/{importer_name}/{source_id}", response_class=HTMLResponse)
async def import_tasks(request: Request, importer_name: str, source_id: str):
    importer = task_manager.importers.get(importer_name)
    if not importer:
        raise HTTPException(status_code=404, detail="Importer not found")

    tasks = importer.get_tasks(source_id)
    state.tasks.extend(tasks)

    return templates.TemplateResponse(
        "components/task_table.html",
        {
            "request": request,
            "tasks": sorted(state.tasks, key=lambda x: x.due_date or datetime.max)
        }
    )


@app.get("/tasks", response_class=HTMLResponse)
async def get_tasks(request: Request):
    return templates.TemplateResponse(
        "components/task_table.html",
        {
            "request": request,
            "tasks": sorted(state.tasks, key=lambda x: x.due_date or datetime.max)
        }
    )


@app.post("/clear-tasks", response_class=HTMLResponse)
async def clear_tasks(request: Request):
    state.tasks = []
    return templates.TemplateResponse(
        "components/task_table.html",
        {"request": request, "tasks": []}
    )


@app.post("/summarize", response_class=HTMLResponse)
async def summarize_tasks(
        request: Request,
        prompt: str = Form(DEFAULT_PROMPT)
):
    if not state.tasks:
        return templates.TemplateResponse(
            "components/summary.html",
            {
                "request": request,
                "summary": "No tasks available to summarize",
                "error": True
            }
        )

    try:
        # Prepare tasks data for the prompt
        tasks_text = "\n".join([
            f"- {task.title} (Due: {task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else 'No due date'}, "
            f"Status: {task.status}, Source: {task.source}, "
            f"Assignees: {', '.join(task.assignees) if task.assignees else 'None'})"
            for task in state.tasks
        ])

        # Create the full prompt
        full_prompt = f"{prompt}\n\nTasks:\n{tasks_text}"

        # Get summary from Claude
        response = await anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": full_prompt
            }]
        )

        summary = response.content[0].text

        return templates.TemplateResponse(
            "components/summary.html",
            {
                "request": request,
                "summary": summary,
                "error": False
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "components/summary.html",
            {
                "request": request,
                "summary": f"Error generating summary: {str(e)}",
                "error": True
            }
        )
