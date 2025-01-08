---
marp: true
title: New Year New Data
theme: gaia
paginate: true
---

# New Year New Data 🎉
## Building Your Personal Task Integration Hub with Python

A workshop for Python beginners and intermediate developers
January 2025

![qr_code:https://github.com/octaflop/new-year-new-data](../tools/qrcode.svg)

---

# Workshop Overview 🗺️

<!-- eta: 5min -->

## What We'll Build

- A personal task hub that integrates multiple data sources
- Real-time data visualization and analysis
- AI-powered task summarization
- Modern web interface with zero page refreshes

---

# Act 1: Data Structure Foundations 🏗️

<!-- eta: 15min -->

## The Building Blocks

- Understanding data classes
- Type hints for better code
- Abstract base classes
- The power of inheritance

---

# Your First Data Class 📦

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class Task:
    title: str
    status: str
    due_date: Optional[datetime]
    assignees: List[str]
    labels: List[str]
    source: str
```

---

# Building the Importer Interface 🔄

<!-- eta: 20min -->

## Abstract Base Classes

```python
from abc import ABC, abstractmethod

class DataImporter(ABC):
    @abstractmethod
    def authenticate(self) -> bool:
        pass
    
    @abstractmethod
    def get_tasks(self, source_id: str) -> List[Task]:
        pass
```

---

# Act 2: Real APIs in Action 🌐

<!-- eta: 25min -->

## Working with External Services

- Trello API integration
- Google Calendar synchronization
- Environment variables for security
- Error handling patterns

---

# Implementing the Trello Importer

```python
class TrelloImporter(DataImporter):
    def __init__(self):
        self.api_key = os.getenv('TRELLO_API_KEY')
        self.token = os.getenv('TRELLO_TOKEN')
        
    def get_tasks(self, board_id: str) -> List[Task]:
        url = f"{self.base_url}/boards/{board_id}/cards"
        response = requests.get(url, params=self.auth_params)
        return [self._convert_to_task(card) 
                for card in response.json()]
```

---

# Act 3: Modern Web Interface ✨

<!-- eta: 30min -->

## FastAPI + HTMX Magic

- FastAPI for modern Python web development
- HTMX for dynamic updates
- Jinja2 templates
- Real-time interactivity

---

# Setting Up FastAPI 🚀

```python
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/sources/{importer_name}")
async def get_sources(request: Request, 
                     importer_name: str):
    importer = task_manager.importers[importer_name]
    sources = importer.get_available_sources()
    return templates.TemplateResponse(
        "source_list.html",
        {"request": request, "sources": sources}
    )
```

---

# HTMX Integration 🔄

```html
<button
    hx-get="/sources/trello"
    hx-target="#trello-sources"
    hx-indicator="#loader"
    class="bg-blue-500 text-white px-4 py-2 rounded">
    Load Boards
</button>

<div id="trello-sources" class="mt-4">
    <!-- Dynamic content here -->
</div>
```

---

# Act 4: AI Integration 🤖

<!-- eta: 20min -->

## Adding Intelligence

- Task analysis with Claude
- Natural language summaries
- Pattern recognition
- Priority suggestions

---

# Claude Integration Example

```python
@app.post("/summarize")
async def summarize_tasks(request: Request,
                         prompt: str = Form(DEFAULT_PROMPT)):
    tasks_text = format_tasks_for_analysis(state.tasks)
    response = await anthropic.messages.create(
        model="claude-3-opus-20240229",
        messages=[{
            "role": "user",
            "content": f"{prompt}\n\n{tasks_text}"
        }]
    )
    return templates.TemplateResponse(
        "summary.html",
        {"request": request, 
         "summary": response.content[0].text}
    )
```

---

# Best Practices 🎯

## Making Your Code Production-Ready

- Environment variables for configuration
- Proper error handling
- Type hints everywhere
- Modular design
- Documentation

---

# Next Steps 🚀

## Extending Your Application

- Add more data sources (GitHub, Notion, etc.)
- Implement data persistence
- Add authentication
- Create custom visualizations
- Build automation rules

---

# Resources 📚

- FastAPI Documentation: fastapi.tiangolo.com
- HTMX: htmx.org
- Anthropic API Docs: docs.anthropic.com
- [This Project Repository](https://github.com/octaflop/new-year-new-data)

---

# Thank You! 🙏

## Contact & Questions

- Workshop materials will be available online
- Follow-up sessions available
- Join our Discord community
- Happy coding! 🐍✨