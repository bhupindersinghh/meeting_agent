import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from services.llm_service import LLMService
from services.voice_service import VoiceService
from services.calendar_service import GoogleCalendarService
from services.time_parsing_service import TimeParsingService
from models.chatbot_models import (
    ConversationContext, 
    ConversationState, 
    MeetingRequest, 
    TimeSlot,
    MessageRequest,
    MessageResponse,
    CalendarConfig,
    VoiceConfig
)

class ConversationEngine:
    def __init__(self):
        self.llm_service = LLMService()
        self.voice_service = VoiceService()
        self.calendar_service = GoogleCalendarService()
        self.time_parser = TimeParsingService()
        self.calendar_config = CalendarConfig()
        self.voice_config = VoiceConfig()
        
        # In-memory storage for conversation contexts
        self.contexts: Dict[str, ConversationContext] = {}
    
    async def process_message(self, request: MessageRequest) -> MessageResponse:
        """Process a user message and return a response"""
        
        # Get or create conversation context
        context = self._get_or_create_context(request.session_id)
        
        # Handle voice input
        if request.is_voice and request.audio_data:
            user_input = await self.voice_service.speech_to_text(request.audio_data)
        else:
            user_input = request.user_query
        
        # Update context with user input
        context.last_user_input = user_input
        context.conversation_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        # Process the conversation
        response_data = await self._process_conversation_turn(context, user_input)
        
        # Update context with assistant response
        context.conversation_history.append({
            "role": "assistant", 
            "content": response_data["response"],
            "timestamp": datetime.now().isoformat()
        })
        
        # Update conversation state
        context.state = response_data["next_state"]
        
        # Generate voice response if needed
        audio_response = None
        if request.is_voice:
            audio_response = await self.voice_service.text_to_speech(
                response_data["response"], 
                self.voice_config
            )
        
        return MessageResponse(
            response=response_data["response"],
            audio_response=audio_response,
            conversation_state=context.state,
            suggested_actions=response_data.get("suggested_actions"),
            requires_clarification=response_data.get("requires_clarification", False)
        )
    
    def _get_or_create_context(self, session_id: str) -> ConversationContext:
        """Get existing context or create new one"""
        if session_id not in self.contexts:
            self.contexts[session_id] = ConversationContext(
                session_id=session_id,
                state=ConversationState.INITIAL
            )
        return self.contexts[session_id]
    
    async def _process_conversation_turn(
        self, 
        context: ConversationContext, 
        user_input: str
    ) -> Dict[str, Any]:
        """Process a single conversation turn"""
        
        # Use LLM to understand the user input
        llm_response = self.llm_service.process_conversation(context, user_input)
        
        # Extract structured information
        extracted_info = llm_response.get("extracted_info", {})
        
        # Update meeting request with extracted information
        if not context.meeting_request:
            context.meeting_request = MeetingRequest(duration_minutes=30)
        
        self._update_meeting_request(context.meeting_request, extracted_info)
        
        # Handle different conversation states
        if context.state == ConversationState.INITIAL:
            return await self._handle_initial_state(context, llm_response)
        
        elif context.state == ConversationState.COLLECTING_DURATION:
            return await self._handle_duration_collection(context, llm_response)
        
        elif context.state == ConversationState.COLLECTING_TIME_PREFERENCE:
            return await self._handle_time_preference_collection(context, llm_response)
        
        elif context.state == ConversationState.CHECKING_AVAILABILITY:
            return await self._handle_availability_check(context, llm_response)
        
        elif context.state == ConversationState.CONFIRMING_SLOT:
            return await self._handle_slot_confirmation(context, llm_response)
        
        elif context.state == ConversationState.SCHEDULING:
            return await self._handle_scheduling(context, llm_response)
        
        else:
            return {
                "response": "I'm not sure how to help with that. Could you please tell me what you need?",
                "next_state": ConversationState.INITIAL,
                "requires_clarification": True
            }
    
    def _update_meeting_request(self, meeting_request: MeetingRequest, extracted_info: Dict[str, Any]):
        """Update meeting request with extracted information"""
        
        if "duration_minutes" in extracted_info:
            meeting_request.duration_minutes = extracted_info["duration_minutes"]
        
        if "preferred_date" in extracted_info:
            meeting_request.preferred_date = datetime.fromisoformat(extracted_info["preferred_date"])
        
        if "preferred_time_range" in extracted_info:
            meeting_request.preferred_time_range = extracted_info["preferred_time_range"]
        
        if "specific_time" in extracted_info:
            meeting_request.specific_time = datetime.fromisoformat(extracted_info["specific_time"])
        
        if "title" in extracted_info:
            meeting_request.title = extracted_info["title"]
        
        if "description" in extracted_info:
            meeting_request.description = extracted_info["description"]
        
        if "attendees" in extracted_info:
            meeting_request.attendees = extracted_info["attendees"]
    
    async def _handle_initial_state(
        self, 
        context: ConversationContext, 
        llm_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle initial conversation state"""
        
        if context.meeting_request and context.meeting_request.duration_minutes:
            return {
                "response": llm_response["response"],
                "next_state": ConversationState.COLLECTING_TIME_PREFERENCE,
                "requires_clarification": False
            }
        else:
            return {
                "response": llm_response["response"],
                "next_state": ConversationState.COLLECTING_DURATION,
                "requires_clarification": True
            }
    
    async def _handle_duration_collection(
        self, 
        context: ConversationContext, 
        llm_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle duration collection state"""
        
        if context.meeting_request and context.meeting_request.duration_minutes:
            return {
                "response": llm_response["response"],
                "next_state": ConversationState.COLLECTING_TIME_PREFERENCE,
                "requires_clarification": False
            }
        else:
            return {
                "response": llm_response["response"],
                "next_state": ConversationState.COLLECTING_DURATION,
                "requires_clarification": True
            }
    
    async def _handle_time_preference_collection(
        self, 
        context: ConversationContext, 
        llm_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle time preference collection state"""
        
        # Use time parser to extract complex time expressions
        time_expression = self.time_parser.parse_time_expression(
            context.last_user_input or "",
            context.current_available_slots
        )
        
        # Resolve the time expression
        resolved_time = self.time_parser.resolve_time_expression(time_expression)
        
        if resolved_time:
            context.meeting_request.specific_time = resolved_time
            return {
                "response": llm_response["response"],
                "next_state": ConversationState.CHECKING_AVAILABILITY,
                "requires_clarification": False
            }
        else:
            return {
                "response": llm_response["response"],
                "next_state": ConversationState.COLLECTING_TIME_PREFERENCE,
                "requires_clarification": True
            }
    
    async def _handle_availability_check(
        self, 
        context: ConversationContext, 
        llm_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle availability checking state"""
        
        if not context.meeting_request:
            return {
                "response": "I need more information to check availability. What kind of meeting are you looking to schedule?",
                "next_state": ConversationState.INITIAL,
                "requires_clarification": True
            }
        
        # Determine time range to check
        start_date = context.meeting_request.specific_time or datetime.now() + timedelta(hours=1)
        end_date = start_date + timedelta(days=7)  # Check next 7 days
        
        # Get available slots
        available_slots = self.calendar_service.get_available_slots(
            start_date,
            end_date,
            context.meeting_request.duration_minutes,
            self.calendar_config
        )
        
        # Filter to available slots only
        context.current_available_slots = [slot for slot in available_slots if slot.is_available]
        
        if context.current_available_slots:
            # Present options to user
            slot_options = context.current_available_slots[:3]  # Top 3 options
            options_text = self._format_slot_options(slot_options)
            
            return {
                "response": f"Great! I found some available times:\n{options_text}\nWhich one works for you?",
                "next_state": ConversationState.CONFIRMING_SLOT,
                "suggested_actions": [f"Option {i+1}" for i in range(len(slot_options))],
                "requires_clarification": False
            }
        else:
            # No available slots - suggest alternatives
            alternatives = self._suggest_alternatives(context)
            return {
                "response": f"I don't see any available slots in the next week. {alternatives}",
                "next_state": ConversationState.COLLECTING_TIME_PREFERENCE,
                "requires_clarification": True
            }
    
    async def _handle_slot_confirmation(
        self, 
        context: ConversationContext, 
        llm_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle slot confirmation state"""
        
        # Parse user's choice
        selected_slot = self._parse_slot_selection(
            context.last_user_input or "",
            context.current_available_slots
        )
        
        if selected_slot:
            context.meeting_request.specific_time = selected_slot.start_time
            return {
                "response": f"Perfect! I'll schedule your {context.meeting_request.duration_minutes}-minute meeting for {selected_slot.start_time.strftime('%A, %B %d at %I:%M %p')}. Is that correct?",
                "next_state": ConversationState.SCHEDULING,
                "requires_clarification": False
            }
        else:
            return {
                "response": "I didn't understand your choice. Please select one of the available options or let me know if you'd like to see different times.",
                "next_state": ConversationState.CONFIRMING_SLOT,
                "requires_clarification": True
            }
    
    async def _handle_scheduling(
        self, 
        context: ConversationContext, 
        llm_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle scheduling state"""
        
        if not context.meeting_request or not context.meeting_request.specific_time:
            return {
                "response": "I need to know when you'd like to schedule the meeting. Please provide a specific time.",
                "next_state": ConversationState.COLLECTING_TIME_PREFERENCE,
                "requires_clarification": True
            }
        
        # Create the calendar event
        event = self.calendar_service.create_event(
            context.meeting_request,
            context.meeting_request.title or "Meeting"
        )
        
        if event:
            return {
                "response": f"Excellent! I've successfully scheduled your meeting for {event.start_time.strftime('%A, %B %d at %I:%M %p')}. You'll receive a calendar invitation shortly.",
                "next_state": ConversationState.COMPLETED,
                "requires_clarification": False
            }
        else:
            return {
                "response": "I encountered an error while scheduling your meeting. Please try again or contact support if the issue persists.",
                "next_state": ConversationState.ERROR,
                "requires_clarification": True
            }
    
    def _format_slot_options(self, slots: List[TimeSlot]) -> str:
        """Format available slots for display"""
        options = []
        for i, slot in enumerate(slots, 1):
            time_str = slot.start_time.strftime('%A, %B %d at %I:%M %p')
            options.append(f"Option {i}: {time_str}")
        return "\n".join(options)
    
    def _parse_slot_selection(self, user_input: str, available_slots: List[TimeSlot]) -> Optional[TimeSlot]:
        """Parse user's slot selection"""
        
        # Look for option numbers
        import re
        option_match = re.search(r'option\s+(\d+)', user_input.lower())
        if option_match:
            option_num = int(option_match.group(1))
            if 1 <= option_num <= len(available_slots):
                return available_slots[option_num - 1]
        
        # Look for time references
        for slot in available_slots:
            time_str = slot.start_time.strftime('%I:%M %p').lower()
            if time_str in user_input.lower():
                return slot
        
        return None
    
    def _suggest_alternatives(self, context: ConversationContext) -> str:
        """Suggest alternative times when no slots are available"""
        
        suggestions = [
            "Would you like to try a different time of day?",
            "How about scheduling for next week?",
            "Would a shorter meeting duration work?",
            "Would you prefer to schedule for a different day?"
        ]
        
        return " ".join(suggestions[:2])  # Return first 2 suggestions
    
    def get_conversation_context(self, session_id: str) -> Optional[ConversationContext]:
        """Get conversation context for a session"""
        return self.contexts.get(session_id)
    
    def clear_conversation_context(self, session_id: str) -> bool:
        """Clear conversation context for a session"""
        if session_id in self.contexts:
            del self.contexts[session_id]
            return True
        return False
