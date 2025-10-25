import re
from datetime import datetime, timedelta, time
from typing import Optional, Dict, Any, List, Tuple
from dateutil import parser, relativedelta
import pytz
from models.chatbot_models import CalendarEvent

class TimeParsingService:
    def __init__(self, timezone: str = "UTC"):
        self.timezone = pytz.timezone(timezone)
        self.now = datetime.now(self.timezone)
        
        # Time range patterns
        self.time_ranges = {
            "morning": (6, 12),
            "afternoon": (12, 17),
            "evening": (17, 22),
            "night": (22, 6)
        }
        
        # Relative time patterns
        self.relative_patterns = {
            r'\btomorrow\b': 1,
            r'\bnext week\b': 7,
            r'\bnext month\b': 30,
            r'\bin (\d+) days?\b': lambda m: int(m.group(1)),
            r'\bin (\d+) weeks?\b': lambda m: int(m.group(1)) * 7,
            r'\bin (\d+) months?\b': lambda m: int(m.group(1)) * 30
        }
    
    def parse_time_expression(
        self, 
        text: str, 
        context_events: List[CalendarEvent] = None
    ) -> Dict[str, Any]:
        """Parse complex time expressions from natural language"""
        
        result = {
            "specific_time": None,
            "preferred_date": None,
            "preferred_time_range": None,
            "relative_offset": None,
            "deadline_reference": None,
            "context_event": None,
            "confidence": 0.0
        }
        
        # Check for specific times
        specific_time = self._extract_specific_time(text)
        if specific_time:
            result["specific_time"] = specific_time
            result["confidence"] += 0.4
        
        # Check for date references
        date_ref = self._extract_date_reference(text)
        if date_ref:
            result["preferred_date"] = date_ref
            result["confidence"] += 0.3
        
        # Check for time ranges
        time_range = self._extract_time_range(text)
        if time_range:
            result["preferred_time_range"] = time_range
            result["confidence"] += 0.2
        
        # Check for relative times
        relative = self._extract_relative_time(text)
        if relative:
            result["relative_offset"] = relative
            result["confidence"] += 0.3
        
        # Check for deadline references
        deadline = self._extract_deadline_reference(text, context_events)
        if deadline:
            result["deadline_reference"] = deadline
            result["confidence"] += 0.4
        
        # Check for context event references
        context_event = self._extract_context_event(text, context_events)
        if context_event:
            result["context_event"] = context_event
            result["confidence"] += 0.4
        
        return result
    
    def _extract_specific_time(self, text: str) -> Optional[datetime]:
        """Extract specific times like '2 PM', '9:30 AM'"""
        
        # Pattern for time with AM/PM
        time_pattern = r'\b(\d{1,2}):?(\d{2})?\s*(AM|PM|am|pm)\b'
        match = re.search(time_pattern, text)
        
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            period = match.group(3).upper()
            
            # Convert to 24-hour format
            if period == "PM" and hour != 12:
                hour += 12
            elif period == "AM" and hour == 12:
                hour = 0
            
            # Use today's date as default
            today = self.now.date()
            return datetime.combine(today, time(hour, minute)).replace(tzinfo=self.timezone)
        
        # Pattern for 24-hour format
        time_24_pattern = r'\b(\d{1,2}):(\d{2})\b'
        match = re.search(time_24_pattern, text)
        
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                today = self.now.date()
                return datetime.combine(today, time(hour, minute)).replace(tzinfo=self.timezone)
        
        return None
    
    def _extract_date_reference(self, text: str) -> Optional[datetime]:
        """Extract date references like 'June 20th', 'next Friday'"""
        
        try:
            # Try parsing with dateutil
            parsed_date = parser.parse(text, fuzzy=True)
            if parsed_date:
                return parsed_date.replace(tzinfo=self.timezone)
        except:
            pass
        
        # Handle specific patterns
        patterns = {
            r'\btoday\b': self.now.date(),
            r'\btomorrow\b': (self.now + timedelta(days=1)).date(),
            r'\byesterday\b': (self.now - timedelta(days=1)).date(),
            r'\bnext monday\b': self._get_next_weekday(0),
            r'\bnext tuesday\b': self._get_next_weekday(1),
            r'\bnext wednesday\b': self._get_next_weekday(2),
            r'\bnext thursday\b': self._get_next_weekday(3),
            r'\bnext friday\b': self._get_next_weekday(4),
            r'\bnext saturday\b': self._get_next_weekday(5),
            r'\bnext sunday\b': self._get_next_weekday(6)
        }
        
        for pattern, date in patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                return datetime.combine(date, time(9, 0)).replace(tzinfo=self.timezone)
        
        return None
    
    def _extract_time_range(self, text: str) -> Optional[str]:
        """Extract time ranges like 'morning', 'afternoon', 'evening'"""
        
        text_lower = text.lower()
        
        for range_name in self.time_ranges.keys():
            if range_name in text_lower:
                return range_name
        
        return None
    
    def _extract_relative_time(self, text: str) -> Optional[timedelta]:
        """Extract relative time expressions"""
        
        for pattern, offset_func in self.relative_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if callable(offset_func):
                    days = offset_func(match)
                else:
                    days = offset_func
                return timedelta(days=days)
        
        return None
    
    def _extract_deadline_reference(
        self, 
        text: str, 
        context_events: List[CalendarEvent]
    ) -> Optional[datetime]:
        """Extract deadline references like 'before my flight at 6 PM'"""
        
        # Look for "before" or "after" patterns
        before_pattern = r'\bbefore\s+(.+)'
        after_pattern = r'\bafter\s+(.+)'
        
        before_match = re.search(before_pattern, text, re.IGNORECASE)
        after_match = re.search(after_pattern, text, re.IGNORECASE)
        
        if before_match or after_match:
            reference_text = (before_match or after_match).group(1)
            
            # Try to find matching event in context
            for event in context_events:
                if any(word in event.title.lower() for word in reference_text.lower().split()):
                    if before_match:
                        # Return time before the event
                        return event.start_time - timedelta(hours=1)
                    else:
                        # Return time after the event
                        return event.end_time + timedelta(hours=1)
        
        return None
    
    def _extract_context_event(
        self, 
        text: str, 
        context_events: List[CalendarEvent]
    ) -> Optional[CalendarEvent]:
        """Extract references to specific events"""
        
        # Look for event titles in the text
        for event in context_events:
            event_words = event.title.lower().split()
            text_words = text.lower().split()
            
            # Check if any significant words match
            matches = sum(1 for word in event_words if word in text_words)
            if matches >= 2:  # At least 2 words match
                return event
        
        return None
    
    def _get_next_weekday(self, weekday: int) -> datetime.date:
        """Get the next occurrence of a specific weekday"""
        days_ahead = weekday - self.now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return (self.now + timedelta(days=days_ahead)).date()
    
    def resolve_time_expression(
        self, 
        expression: Dict[str, Any], 
        context_events: List[CalendarEvent] = None
    ) -> Optional[datetime]:
        """Resolve a time expression to a specific datetime"""
        
        # Priority order: specific_time > deadline_reference > context_event > preferred_date > relative_offset
        
        if expression.get("specific_time"):
            return expression["specific_time"]
        
        if expression.get("deadline_reference"):
            return expression["deadline_reference"]
        
        if expression.get("context_event"):
            event = expression["context_event"]
            # Return 1 hour before the event
            return event.start_time - timedelta(hours=1)
        
        if expression.get("preferred_date"):
            base_date = expression["preferred_date"]
            if expression.get("preferred_time_range"):
                time_range = self.time_ranges.get(expression["preferred_time_range"])
                if time_range:
                    hour = (time_range[0] + time_range[1]) // 2  # Middle of range
                    return base_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            return base_date
        
        if expression.get("relative_offset"):
            return self.now + expression["relative_offset"]
        
        return None
    
    def suggest_alternatives(
        self, 
        unavailable_time: datetime, 
        duration_minutes: int = 60
    ) -> List[datetime]:
        """Suggest alternative times when a slot is unavailable"""
        
        alternatives = []
        
        # Same day alternatives
        for hour_offset in [1, 2, 3, -1, -2, -3]:
            alt_time = unavailable_time + timedelta(hours=hour_offset)
            if self._is_valid_time(alt_time):
                alternatives.append(alt_time)
        
        # Next day alternatives
        next_day = unavailable_time + timedelta(days=1)
        if self._is_valid_time(next_day):
            alternatives.append(next_day)
        
        # Same time next week
        next_week = unavailable_time + timedelta(weeks=1)
        if self._is_valid_time(next_week):
            alternatives.append(next_week)
        
        return alternatives[:5]  # Return top 5 alternatives
    
    def _is_valid_time(self, dt: datetime) -> bool:
        """Check if a datetime is valid for scheduling"""
        
        # Check if it's in the future
        if dt <= self.now:
            return False
        
        # Check if it's during reasonable hours (6 AM to 10 PM)
        hour = dt.hour
        if not (6 <= hour <= 22):
            return False
        
        # Check if it's a weekday (Monday to Friday)
        if dt.weekday() >= 5:  # Saturday or Sunday
            return False
        
        return True
