from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import uvicorn
from typing import List, Dict, Optional
from datetime import datetime

# Import our task manager system
from task_importer import TaskManager, Task  # Assuming previous code is in task_importer.py

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Initialize TaskManager
task_manager = TaskManager()


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
