import os
import json
from typing import Dict, List, Optional, Any
from openai import OpenAI
from datetime import datetime, timedelta
from models.chatbot_models import (
    ConversationContext, 
    ConversationState, 
    MeetingRequest, 
    TimeSlot,
    MessageRequest,
    MessageResponse
)

class LLMService:
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4"
    
    def process_conversation(
        self, 
        context: ConversationContext, 
        user_input: str
    ) -> Dict[str, Any]:
        """Process user input and return conversation response"""
        
        system_prompt = self._build_system_prompt()
        conversation_history = self._build_conversation_history(context)
        
        messages = [
            {"role": "system", "content": system_prompt},
            *conversation_history,
            {"role": "user", "content": user_input}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            assistant_message = response.choices[0].message.content
            
            # Parse the response to extract structured information
            parsed_response = self._parse_llm_response(assistant_message, context)
            
            return parsed_response
            
        except Exception as e:
            print(f"Error in LLM processing: {e}")
            return {
                "response": "I'm sorry, I encountered an error. Could you please try again?",
                "next_state": ConversationState.ERROR,
                "requires_clarification": True,
                "extracted_info": {}
            }
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the AI assistant"""
        return """
You are a Smart Scheduler AI Agent that helps users schedule meetings. Your role is to:

1. Understand user requirements for meeting scheduling
2. Ask clarifying questions when information is missing
3. Provide helpful suggestions and alternatives
4. Maintain a natural, conversational tone

Key capabilities:
- Extract meeting duration, preferred times, and other requirements from natural language
- Handle complex time expressions like "sometime next week", "after my 5 PM meeting"
- Suggest alternatives when requested times are unavailable
- Remember context across the conversation

Conversation flow:
1. Initial: Greet and ask what they need
2. Collecting Duration: Ask for meeting duration if not provided
3. Collecting Time Preference: Ask for preferred time/date
4. Checking Availability: Search for available slots
5. Confirming Slot: Present options and get confirmation
6. Scheduling: Create the meeting
7. Completed: Confirm successful scheduling

Always be helpful, clear, and proactive in suggesting alternatives.
"""
    
    def _build_conversation_history(self, context: ConversationContext) -> List[Dict[str, str]]:
        """Build conversation history for context"""
        history = []
        
        for entry in context.conversation_history[-10:]:  # Last 10 exchanges
            if entry.get("role") == "user":
                history.append({"role": "user", "content": entry.get("content", "")})
            elif entry.get("role") == "assistant":
                history.append({"role": "assistant", "content": entry.get("content", "")})
        
        return history
    
    def _parse_llm_response(
        self, 
        response: str, 
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Parse LLM response to extract structured information"""
        
        # Extract meeting information using a follow-up call
        extraction_prompt = f"""
Extract structured information from this user input: "{context.last_user_input or ''}"

Return a JSON object with:
- duration_minutes: integer (if mentioned)
- preferred_date: ISO datetime string (if mentioned)
- preferred_time_range: string like "morning", "afternoon", "evening" (if mentioned)
- specific_time: ISO datetime (if mentioned)
- title: string (if mentioned)
- description: string (if mentioned)
- attendees: array of email strings (if mentioned)

Only include fields that are explicitly mentioned. Return empty object {{}} if no structured info found.
"""
        
        try:
            extraction_response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data extraction assistant. Return only valid JSON."},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            extracted_info = json.loads(extraction_response.choices[0].message.content)
        except:
            extracted_info = {}
        
        # Determine next state based on current state and extracted info
        next_state = self._determine_next_state(context.state, extracted_info)
        
        return {
            "response": response,
            "next_state": next_state,
            "extracted_info": extracted_info,
            "requires_clarification": self._needs_clarification(context.state, extracted_info)
        }
    
    def _determine_next_state(
        self, 
        current_state: ConversationState, 
        extracted_info: Dict[str, Any]
    ) -> ConversationState:
        """Determine the next conversation state based on current state and extracted info"""
        
        if current_state == ConversationState.INITIAL:
            if extracted_info.get("duration_minutes"):
                return ConversationState.COLLECTING_TIME_PREFERENCE
            else:
                return ConversationState.COLLECTING_DURATION
        
        elif current_state == ConversationState.COLLECTING_DURATION:
            if extracted_info.get("duration_minutes"):
                return ConversationState.COLLECTING_TIME_PREFERENCE
            else:
                return ConversationState.COLLECTING_DURATION
        
        elif current_state == ConversationState.COLLECTING_TIME_PREFERENCE:
            if extracted_info.get("preferred_date") or extracted_info.get("preferred_time_range"):
                return ConversationState.CHECKING_AVAILABILITY
            else:
                return ConversationState.COLLECTING_TIME_PREFERENCE
        
        elif current_state == ConversationState.CHECKING_AVAILABILITY:
            return ConversationState.CONFIRMING_SLOT
        
        elif current_state == ConversationState.CONFIRMING_SLOT:
            return ConversationState.SCHEDULING
        
        elif current_state == ConversationState.SCHEDULING:
            return ConversationState.COMPLETED
        
        return current_state
    
    def _needs_clarification(
        self, 
        current_state: ConversationState, 
        extracted_info: Dict[str, Any]
    ) -> bool:
        """Determine if clarification is needed"""
        
        if current_state == ConversationState.COLLECTING_DURATION:
            return not extracted_info.get("duration_minutes")
        
        elif current_state == ConversationState.COLLECTING_TIME_PREFERENCE:
            return not (extracted_info.get("preferred_date") or 
                       extracted_info.get("preferred_time_range") or 
                       extracted_info.get("specific_time"))
        
        return False
    
    def generate_alternative_suggestions(
        self, 
        unavailable_slots: List[TimeSlot], 
        context: ConversationContext
    ) -> List[str]:
        """Generate alternative time suggestions when slots are unavailable"""
        
        suggestions = []
        
        # Analyze the conflicts
        conflict_reasons = [slot.conflict_reason for slot in unavailable_slots if slot.conflict_reason]
        
        if any("morning" in reason.lower() for reason in conflict_reasons):
            suggestions.append("How about afternoon or evening times?")
        
        if any("afternoon" in reason.lower() for reason in conflict_reasons):
            suggestions.append("Would morning or evening work better?")
        
        if any("evening" in reason.lower() for reason in conflict_reasons):
            suggestions.append("How about morning or afternoon times?")
        
        # Suggest different days
        suggestions.extend([
            "Would tomorrow work instead?",
            "How about next week?",
            "Would a different day this week be better?"
        ])
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def extract_time_expressions(self, text: str) -> Dict[str, Any]:
        """Extract complex time expressions from natural language"""
        
        prompt = f"""
Extract time-related information from this text: "{text}"

Look for:
- Relative times: "tomorrow", "next week", "in 2 days"
- Time ranges: "morning", "afternoon", "evening"
- Specific times: "2 PM", "9:30 AM"
- Deadlines: "before my flight at 6 PM", "after my meeting"
- Date references: "June 20th", "next Friday"

Return JSON with:
- relative_time: string
- time_range: string
- specific_time: string
- deadline_reference: string
- date_reference: string
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Extract time information. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            return json.loads(response.choices[0].message.content)
        except:
            return {}
