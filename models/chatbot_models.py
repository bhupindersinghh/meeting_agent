from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

class ConversationState(str, Enum):
    INITIAL = "initial"
    COLLECTING_DURATION = "collecting_duration"
    COLLECTING_TIME_PREFERENCE = "collecting_time_preference"
    CHECKING_AVAILABILITY = "checking_availability"
    CONFIRMING_SLOT = "confirming_slot"
    SCHEDULING = "scheduling"
    COMPLETED = "completed"
    ERROR = "error"

class MessageRequest(BaseModel):
    user_query: str
    session_id: str
    audio_data: Optional[str] = None  # Base64 encoded audio
    is_voice: bool = False

class MessageResponse(BaseModel):
    response: str
    audio_response: Optional[str] = None  # Base64 encoded audio
    conversation_state: ConversationState
    suggested_actions: Optional[List[str]] = None
    requires_clarification: bool = False

class CalendarEvent(BaseModel):
    id: Optional[str] = None
    title: str
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None
    attendees: Optional[List[str]] = None

class TimeSlot(BaseModel):
    start_time: datetime
    end_time: datetime
    is_available: bool = True
    conflict_reason: Optional[str] = None

class MeetingRequest(BaseModel):
    duration_minutes: int
    preferred_date: Optional[datetime] = None
    preferred_time_range: Optional[str] = None  # "morning", "afternoon", "evening"
    specific_time: Optional[datetime] = None
    attendees: Optional[List[str]] = None
    title: Optional[str] = None
    description: Optional[str] = None

class ConversationContext(BaseModel):
    session_id: str
    state: ConversationState
    meeting_request: Optional[MeetingRequest] = None
    conversation_history: List[Dict[str, Any]] = []
    current_available_slots: List[TimeSlot] = []
    last_user_input: Optional[str] = None
    clarification_needed: Optional[str] = None

class VoiceConfig(BaseModel):
    voice_id: str = "alloy"
    speed: float = 1.0
    pitch: float = 1.0

class CalendarConfig(BaseModel):
    timezone: str = "UTC"
    working_hours_start: int = 9
    working_hours_end: int = 17
    working_days: List[int] = [0, 1, 2, 3, 4]  # Monday to Friday