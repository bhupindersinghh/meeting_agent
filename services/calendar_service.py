import os
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytz
from models.chatbot_models import CalendarEvent, TimeSlot, MeetingRequest, CalendarConfig

class GoogleCalendarService:
    def __init__(self, credentials_file: str = "credentials.json", token_file: str = "token.json"):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.credentials = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        
        creds = None
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if os.path.exists(self.credentials_file):
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES)
                    creds = flow.run_local_server(port=0)
                else:
                    raise FileNotFoundError(f"Credentials file {self.credentials_file} not found")
            
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.credentials = creds
        self.service = build('calendar', 'v3', credentials=creds)
    
    def get_available_slots(
        self, 
        start_date: datetime, 
        end_date: datetime, 
        duration_minutes: int,
        config: CalendarConfig
    ) -> List[TimeSlot]:
        """Get available time slots within the specified date range"""
        try:
            # Convert to RFC3339 format for Google Calendar API
            time_min = start_date.isoformat() + 'Z'
            time_max = end_date.isoformat() + 'Z'
            
            # Get busy times
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Generate time slots
            available_slots = []
            current_time = start_date
            
            while current_time < end_date:
                # Check if current time is within working hours
                if self._is_working_hour(current_time, config):
                    slot_end = current_time + timedelta(minutes=duration_minutes)
                    
                    # Check for conflicts
                    is_available, conflict_reason = self._check_slot_availability(
                        current_time, slot_end, events
                    )
                    
                    slot = TimeSlot(
                        start_time=current_time,
                        end_time=slot_end,
                        is_available=is_available,
                        conflict_reason=conflict_reason
                    )
                    available_slots.append(slot)
                
                # Move to next 30-minute slot
                current_time += timedelta(minutes=30)
            
            return available_slots
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []
    
    def _is_working_hour(self, dt: datetime, config: CalendarConfig) -> bool:
        """Check if datetime is within working hours"""
        # Convert to local timezone
        local_tz = pytz.timezone(config.timezone)
        local_dt = dt.astimezone(local_tz)
        
        # Check if it's a working day
        if local_dt.weekday() not in config.working_days:
            return False
        
        # Check if it's within working hours
        hour = local_dt.hour
        return config.working_hours_start <= hour < config.working_hours_end
    
    def _check_slot_availability(
        self, 
        start_time: datetime, 
        end_time: datetime, 
        events: List[Dict]
    ) -> tuple[bool, Optional[str]]:
        """Check if a time slot conflicts with existing events"""
        for event in events:
            event_start = datetime.fromisoformat(
                event['start'].get('dateTime', event['start'].get('date'))
            )
            event_end = datetime.fromisoformat(
                event['end'].get('dateTime', event['end'].get('date'))
            )
            
            # Check for overlap
            if (start_time < event_end and end_time > event_start):
                return False, f"Conflicts with: {event.get('summary', 'Unknown event')}"
        
        return True, None
    
    def create_event(self, meeting_request: MeetingRequest, title: str = "Meeting") -> Optional[CalendarEvent]:
        """Create a new calendar event"""
        try:
            if not meeting_request.specific_time:
                raise ValueError("Specific time is required to create an event")
            
            start_time = meeting_request.specific_time
            end_time = start_time + timedelta(minutes=meeting_request.duration_minutes)
            
            event = {
                'summary': title,
                'description': meeting_request.description or f"{meeting_request.duration_minutes}-minute meeting",
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
            }
            
            if meeting_request.attendees:
                event['attendees'] = [{'email': email} for email in meeting_request.attendees]
            
            created_event = self.service.events().insert(
                calendarId='primary', 
                body=event
            ).execute()
            
            return CalendarEvent(
                id=created_event['id'],
                title=title,
                start_time=start_time,
                end_time=end_time,
                description=meeting_request.description,
                attendees=meeting_request.attendees
            )
            
        except HttpError as error:
            print(f"An error occurred while creating event: {error}")
            return None
    
    def get_events_in_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[CalendarEvent]:
        """Get all events within a date range"""
        try:
            time_min = start_date.isoformat() + 'Z'
            time_max = end_date.isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            calendar_events = []
            
            for event in events:
                start_time = datetime.fromisoformat(
                    event['start'].get('dateTime', event['start'].get('date'))
                )
                end_time = datetime.fromisoformat(
                    event['end'].get('dateTime', event['end'].get('date'))
                )
                
                attendees = []
                if 'attendees' in event:
                    attendees = [att.get('email') for att in event['attendees']]
                
                calendar_events.append(CalendarEvent(
                    id=event.get('id'),
                    title=event.get('summary', 'No title'),
                    start_time=start_time,
                    end_time=end_time,
                    description=event.get('description'),
                    attendees=attendees
                ))
            
            return calendar_events
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []
    
    def find_events_by_title(self, title: str, start_date: datetime, end_date: datetime) -> List[CalendarEvent]:
        """Find events by title within a date range"""
        events = self.get_events_in_range(start_date, end_date)
        return [event for event in events if title.lower() in event.title.lower()]
