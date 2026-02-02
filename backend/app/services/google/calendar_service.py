"""Google Calendar integration service."""

from datetime import datetime, timedelta
from typing import Optional
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/calendar.readonly'
]


class GoogleCalendarService:
    """Service for reading events from Google Calendar."""

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

    def list_events(
        self,
        calendar_id: str = 'primary',
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_results: int = 100
    ) -> list[dict]:
        """
        List calendar events within a date range.

        Args:
            calendar_id: Calendar ID (default: 'primary' or email address)
            start_date: Start of date range (default: now)
            end_date: End of date range (default: 14 days from start)
            max_results: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        try:
            if not start_date:
                start_date = datetime.utcnow()
            if not end_date:
                end_date = start_date + timedelta(days=14)

            service = build('calendar', 'v3', credentials=self.creds)

            # Convert to RFC3339 timestamp
            time_min = start_date.isoformat() + 'Z'
            time_max = end_date.isoformat() + 'Z'

            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            # Parse and normalize events
            normalized_events = []
            for event in events:
                normalized_event = self._normalize_event(event, calendar_id)
                if normalized_event:
                    normalized_events.append(normalized_event)

            return normalized_events

        except Exception as e:
            print(f"Error reading calendar {calendar_id}: {e}")
            raise

    def _normalize_event(self, event: dict, calendar_id: str) -> Optional[dict]:
        """
        Normalize a Google Calendar event to our format.

        Args:
            event: Raw event from Google Calendar API
            calendar_id: The calendar this event belongs to

        Returns:
            Normalized event dictionary or None if event should be skipped
        """
        # Skip cancelled events
        if event.get('status') == 'cancelled':
            return None

        # Parse start and end times
        start = event.get('start', {})
        end = event.get('end', {})

        # Handle all-day events
        is_all_day = 'date' in start

        if is_all_day:
            start_time = datetime.fromisoformat(start['date'])
            end_time = datetime.fromisoformat(end['date'])
        else:
            # Parse datetime with timezone
            start_time_str = start.get('dateTime', '')
            end_time_str = end.get('dateTime', '')

            # Remove timezone info for UTC storage (simplified)
            if start_time_str:
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            else:
                return None

            if end_time_str:
                end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
            else:
                end_time = start_time + timedelta(hours=1)  # Default 1 hour

        return {
            'google_event_id': event['id'],
            'title': event.get('summary', '(No title)'),
            'description': event.get('description'),
            'start_time': start_time,
            'end_time': end_time,
            'is_all_day': is_all_day,
            'is_recurring': 'recurringEventId' in event,
            'recurrence_rule': event.get('recurrence', [None])[0] if event.get('recurrence') else None,
            'calendar_id': calendar_id,
            'location': event.get('location'),
            'attendees': [
                {'email': a.get('email'), 'status': a.get('responseStatus')}
                for a in event.get('attendees', [])
            ],
            'html_link': event.get('htmlLink'),
        }

    def get_calendar_list(self) -> list[dict]:
        """
        Get list of all calendars accessible to the user.

        Returns:
            List of calendar dictionaries with id, summary, and description
        """
        try:
            service = build('calendar', 'v3', credentials=self.creds)
            calendar_list = service.calendarList().list().execute()

            calendars = []
            for calendar in calendar_list.get('items', []):
                calendars.append({
                    'id': calendar['id'],
                    'summary': calendar.get('summary', 'Unnamed Calendar'),
                    'description': calendar.get('description'),
                    'primary': calendar.get('primary', False),
                    'access_role': calendar.get('accessRole'),
                    'background_color': calendar.get('backgroundColor'),
                })

            return calendars

        except Exception as e:
            print(f"Error fetching calendar list: {e}")
            raise
