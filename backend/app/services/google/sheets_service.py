"""Google Sheets integration service."""

from typing import Any, Optional
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/calendar.readonly'
]


class GoogleSheetsService:
    """Service for reading data from Google Sheets."""

    def __init__(self):
        self.creds = None
        self._load_credentials()

    def _load_credentials(self):
        """Load or refresh Google API credentials."""
        token_path = os.path.expanduser('~/.schedule-manager/google_token.json')
        # Try parent directory first (for monorepo structure)
        creds_path = os.getenv('GOOGLE_CREDENTIALS_PATH')
        if not creds_path:
            if os.path.exists('../google_credentials.json'):
                creds_path = '../google_credentials.json'
            else:
                creds_path = './google_credentials.json'

        if os.path.exists(token_path):
            self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists(creds_path):
                    raise FileNotFoundError(
                        f"Google credentials file not found at {creds_path}. "
                        "Please download it from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                self.creds = flow.run_local_server(port=0)

            # Save credentials for next run
            os.makedirs(os.path.dirname(token_path), exist_ok=True)
            with open(token_path, 'w') as token:
                token.write(self.creds.to_json())

    def read_sheet(self, spreadsheet_id: str, range_name: str) -> list[list[Any]]:
        """
        Read data from a Google Sheet.

        Args:
            spreadsheet_id: The ID of the spreadsheet
            range_name: The A1 notation range (e.g., "Sheet1!A1:D10")

        Returns:
            List of rows, where each row is a list of cell values
        """
        try:
            service = build('sheets', 'v4', credentials=self.creds)
            sheet = service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()

            return result.get('values', [])
        except Exception as e:
            print(f"Error reading sheet {spreadsheet_id}: {e}")
            raise

    def read_household_tasks(self, spreadsheet_id: str, range_name: str = "Sheet2!A2:H") -> list[dict]:
        """
        Read household tasks from a Google Sheet.

        Expected columns:
        A: Task Name
        B: Description
        C: Duration (minutes)
        D: Recurrence (daily/weekly/biweekly/monthly)
        E: Priority (low/medium/high/critical)
        F: Preferred Days (comma-separated: Mon, Tue, etc.)
        G: Preferred Time (morning/afternoon/evening/any)
        H: Active (yes/no/true/false)

        Returns:
            List of task dictionaries
        """
        rows = self.read_sheet(spreadsheet_id, range_name)
        tasks = []

        for row in rows:
            if not row or not row[0]:  # Skip empty rows
                continue

            # Parse recurrence - handle "yes"/"no" from sheet
            recurrence_raw = row[3].lower() if len(row) > 3 and row[3] else 'weekly'
            if recurrence_raw in ['yes', 'y', 'true', '1']:
                recurrence = 'daily'
            elif recurrence_raw in ['no', 'n', 'false', '0']:
                recurrence = 'weekly'
            else:
                # Direct value like "daily", "weekly", "biweekly", "monthly"
                recurrence = recurrence_raw

            task = {
                'name': row[0] if len(row) > 0 else '',
                'description': row[1] if len(row) > 1 else None,
                'estimated_duration_minutes': int(row[2]) if len(row) > 2 and row[2] else 60,
                'recurrence': recurrence,
                'priority': row[4].lower() if len(row) > 4 and row[4] else 'medium',
                'preferred_days': self._parse_days(row[5]) if len(row) > 5 and row[5] else [],
                'preferred_time_slots': [row[6].lower()] if len(row) > 6 and row[6] else ['any'],
                'is_active': self._parse_bool(row[7]) if len(row) > 7 else True,
            }

            if task['name']:  # Only add if we have a name
                tasks.append(task)

        return tasks

    def _parse_days(self, day_str: str) -> list[int]:
        """Convert day names to day numbers (0=Monday, 6=Sunday)."""
        day_map = {
            'mon': 0, 'monday': 0,
            'tue': 1, 'tuesday': 1,
            'wed': 2, 'wednesday': 2,
            'thu': 3, 'thursday': 3,
            'fri': 4, 'friday': 4,
            'sat': 5, 'saturday': 5,
            'sun': 6, 'sunday': 6,
        }

        days = []
        for day in day_str.lower().replace(',', ' ').split():
            if day in day_map:
                days.append(day_map[day])

        return days

    def _parse_bool(self, value: str) -> bool:
        """Parse boolean value from string."""
        if isinstance(value, bool):
            return value
        return value.lower() in ('yes', 'true', '1', 'y')
