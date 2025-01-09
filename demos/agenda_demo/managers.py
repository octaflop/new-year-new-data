from datetime import datetime
from typing import List

from rich import Console, box
from rich.table import Table

from demos.agenda_demo.models import TrelloImporter, GoogleCalendarImporter, Task


class TaskManager:
    """Manages different data importers and task display"""

    def __init__(self):
        self.console = Console()
        self.importers = {
            'trello': TrelloImporter(),
            'gcal': GoogleCalendarImporter()
        }

    def display_tasks(self, tasks: List[Task]):
        """Display tasks in a pretty table format"""
        table = Table(
            show_header=True,
            header_style="bold magenta",
            box=box.ROUNDED,
            title="[bold cyan]Tasks Overview[/bold cyan]"
        )

        table.add_column("Title", style="bold", width=40)
        table.add_column("Source", style="cyan")
        table.add_column("Status", style="blue")
        table.add_column("Due Date", style="green")
        table.add_column("Assignees", style="yellow")
        table.add_column("Labels", style="red")

        for task in sorted(tasks, key=lambda x: x.due_date or datetime.max):
            table.add_row(
                task.title,
                task.source,
                task.status,
                task.due_date.strftime("%Y-%m-%d %H:%M") if task.due_date else "No due date",
                "\n".join(task.assignees) or "No assignees",
                "\n".join(task.labels) or "No labels"
            )

        self.console.print(table)

    def run(self):
        """Main execution flow"""
        try:
            all_tasks = []

            # Initialize and authenticate importers
            for name, importer in self.importers.items():
                self.console.print(f"\n[bold]Initializing {name} importer...[/bold]")
                if importer.authenticate():
                    sources = importer.get_available_sources()

                    if not sources:
                        self.console.print(f"[yellow]No sources found for {name}[/yellow]")
                        continue

                    # Display available sources
                    source_table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
                    source_table.add_column("Index", style="bold")
                    source_table.add_column("Source Name", style="cyan")

                    for idx, source in enumerate(sources, 1):
                        source_table.add_row(str(idx), source['name'])

                    self.console.print(f"\n[bold]Available {name} sources:[/bold]")
                    self.console.print(source_table)

                    while True:
                        try:
                            selection = input(f"\nSelect {name} source number (or 0 to skip): ")
                            if selection == "0":
                                break
                            selection = int(selection)
                            if 1 <= selection <= len(sources):
                                selected_source = sources[selection - 1]
                                tasks = importer.get_tasks(selected_source['id'])
                                all_tasks.extend(tasks)
                                break
                            print("Invalid selection. Please try again.")
                        except ValueError:
                            print("Please enter a valid number.")

            if all_tasks:
                self.display_tasks(all_tasks)
            else:
                self.console.print("[yellow]No tasks found from any source[/yellow]")

        except Exception as e:
            self.console.print(f"[red]An unexpected error occurred: {str(e)}[/red]")


if __name__ == "__main__":
    manager = TaskManager()
    manager.run()