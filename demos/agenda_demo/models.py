import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any

import requests

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


@dataclass
class Task:
    """Universal task representation for different data sources"""
    title: str
    status: str
    due_date: Optional[datetime]
    assignees: List[str]
    labels: List[str]
    source: str
    source_id: str
    additional_data: Dict[str, Any] = None


class DataImporter(ABC):
    """Abstract base class for data importers"""

    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the service"""
        pass

    @abstractmethod
    def get_available_sources(self) -> List[Dict[str, str]]:
        """Get available data sources (boards, calendars, etc.)"""
        pass

    @abstractmethod
    def get_tasks(self, source_id: str) -> List[Task]:
        """Get tasks from the specified source"""
        pass


class TrelloImporter(DataImporter):
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('TRELLO_API_KEY')
        self.token = os.getenv('TRELLO_TOKEN')
        self.base_url = "https://api.trello.com/1"
        self.auth_params = {
            'key': self.api_key,
            'token': self.token
        }

    def authenticate(self) -> bool:
        if not self.api_key or not self.token:
            self.console.print("[red]Error: Please set TRELLO_API_KEY and TRELLO_TOKEN in your .env file[/red]")
            return False
        try:
            self.get_available_sources()
            return True
        except requests.exceptions.RequestException:
            return False

    def get_available_sources(self) -> List[Dict[str, str]]:
        url = f"{self.base_url}/members/me/boards"
        response = requests.get(url, params=self.auth_params)
        response.raise_for_status()
        return [{'id': board['id'], 'name': board['name']} for board in response.json()]

    def get_lists(self, board_id: str) -> List[Dict[str, str]]:
        url = f"{self.base_url}/boards/{board_id}/lists"
        response = requests.get(url, params=self.auth_params)
        response.raise_for_status()
        return response.json()

    def get_tasks(self, board_id: str) -> List[Task]:
        url = f"{self.base_url}/boards/{board_id}/cards"
        params = {**self.auth_params, 'members': 'true', 'member_fields': 'fullName'}
        response = requests.get(url, params=params)
        response.raise_for_status()
        cards = response.json()
        lists = {lst['id']: lst['name'] for lst in self.get_lists(board_id)}

        tasks = []
        for card in cards:
            due_date = None
            if card.get('due'):
                due_date = datetime.fromisoformat(card['due'].replace('Z', '+00:00'))

            task = Task(
                title=card['name'],
                status=lists.get(card['idList'], 'Unknown'),
                due_date=due_date,
                assignees=[member['fullName'] for member in card.get('members', [])],
                labels=[label['name'] for label in card.get('labels', [])],
                source='Trello',
                source_id=card['id'],
                additional_data={'url': card['url']}
            )
            tasks.append(task)

        return tasks


class GoogleCalendarImporter(DataImporter):
    def __init__(self):
        super().__init__()
        self.SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        self.creds = None

    def authenticate(self) -> bool:
        try:
            if os.path.exists('token.json'):
                self.creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)

            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', self.SCOPES)
                    self.creds = flow.run_local_server(port=0)
                with open('token.json', 'w') as token:
                    token.write(self.creds.to_json())
            return True
        except Exception as e:
            self.console.print(f"[red]Error authenticating with Google Calendar: {str(e)}[/red]")
            return False

    def get_available_sources(self) -> List[Dict[str, str]]:
        try:
            service = build('calendar', 'v3', credentials=self.creds)
            calendar_list = service.calendarList().list().execute()
            return [{'id': cal['id'], 'name': cal['summary']}
                    for cal in calendar_list.get('items', [])]
        except HttpError as e:
            self.console.print(f"[red]Error fetching calendars: {str(e)}[/red]")
            return []

    def get_tasks(self, calendar_id: str) -> List[Task]:
        try:
            service = build('calendar', 'v3', credentials=self.creds)
            now = datetime.utcnow().isoformat() + 'Z'
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=now,
                maxResults=100,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])

            tasks = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                if start:
                    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                else:
                    start_dt = None

                task = Task(
                    title=event['summary'],
                    status='Scheduled',
                    due_date=start_dt,
                    assignees=[attendee['email'] for attendee in event.get('attendees', [])],
                    labels=[],
                    source='Google Calendar',
                    source_id=event['id'],
                    additional_data={
                        'description': event.get('description', ''),
                        'location': event.get('location', '')
                    }
                )
                tasks.append(task)

            return tasks
        except HttpError as e:
            self.console.print(f"[red]Error fetching events: {str(e)}[/red]")
            return []
